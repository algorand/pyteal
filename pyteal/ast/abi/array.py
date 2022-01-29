from typing import (
    Callable,
    Union,
    Sequence,
    NamedTuple,
    TypeVar,
    Generic,
    Optional,
    cast,
)
from abc import abstractmethod

from ...types import TealType
from ..expr import Expr
from ..seq import Seq
from ..int import Int
from ..bytes import Bytes
from ..if_ import If
from ..for_ import For
from ..unaryexpr import BytesZero, Len
from ..binaryexpr import ExtractUint16
from ..naryexpr import Concat
from ..substring import Extract, Suffix
from ..scratchvar import ScratchVar

from .type import Type
from .tuple import encodeTuple
from .uint import Uint16


class ArrayProperties(NamedTuple):
    has_offsets: bool
    stride: int
    static_length: Optional[int]


def createArrayProperties(
    valueType: Type, static_length: Optional[int]
) -> ArrayProperties:
    if static_length is not None:
        if not valueType.is_dynamic():
            return ArrayProperties(
                has_offsets=False,
                stride=valueType.byte_length_static(),  # TODO: bool support
                static_length=static_length,
            )

        return ArrayProperties(has_offsets=True, stride=2, static_length=static_length)

    tmpProps = createArrayProperties(valueType, 1)
    return ArrayProperties(
        has_offsets=tmpProps.has_offsets, stride=tmpProps.stride, static_length=None
    )


def encodeArray(values: Sequence[Type], props: ArrayProperties) -> Expr:
    tupleEncoding = encodeTuple(values)

    if props.static_length is None:
        length_tmp = Uint16()
        length_prefix = Seq(length_tmp.set(len(values)), length_tmp.encode())
        return Concat(length_prefix, tupleEncoding)

    return tupleEncoding


def arrayLength(encoded: Expr, props: ArrayProperties) -> Expr:
    assert props.static_length is None

    output = Uint16()
    return Seq(
        output.decode(encoded, Int(0), Int(2)),
        output.get(),
    )


T = TypeVar("T", bound=Type)


def indexArray(
    valueType: T,
    encoded: Expr,
    index: Expr,
    output: T,
    props: ArrayProperties,
) -> Expr:
    offsetIndex = Int(props.stride) * index

    if props.static_length is None:
        lengthExpr = arrayLength(encoded, props)
        offsetIndex = offsetIndex + Int(2)
    else:
        lengthExpr = Int(props.static_length)

    if props.has_offsets:
        valueStartRelative = ExtractUint16(encoded, offsetIndex)
        if props.static_length is None:
            valueStart = valueStartRelative + Int(2)
        else:
            valueStart = valueStartRelative
        valueLength = (
            If(index + Int(1) == lengthExpr)
            .Then(lengthExpr * Int(props.stride) - valueStartRelative)
            .Else(ExtractUint16(encoded, offsetIndex + Int(2)) - valueStartRelative)
        )
    else:
        valueStart = offsetIndex
        valueLength = Int(props.stride)

    if not valueType.has_same_type_as(output):
        raise TypeError("Output type does not match value type")

    return output.decode(encoded, valueStart, valueLength)


class Array(Type, Generic[T]):
    def __init__(self, valueType: T, staticLength: Optional[int]) -> None:
        super().__init__(TealType.bytes)
        self._valueType = valueType
        self._props = createArrayProperties(valueType, staticLength)

    def decode(self, encoded: Expr, offset: Expr, length: Expr) -> Expr:
        return self.stored_value.store(Extract(encoded, offset, length))

    def set(self, values: Sequence[T]) -> Expr:
        if not all(self._valueType.has_same_type_as(value) for value in values):
            raise ValueError(
                "Input values do not match type"
            )  # TODO: add more to error message
        return self.stored_value.store(encodeArray(values, self._props))

    def encode(self) -> Expr:
        return self.stored_value.load()

    @abstractmethod
    def length(self) -> Expr:
        pass

    def __getitem__(self, index: Union[int, Expr]) -> "ArrayElement[T]":
        if type(index) is int:
            index = Int(index)
        return ArrayElement(self, cast(Expr, index))

    def forEach(self, action: Callable[[T, Expr], Expr]) -> Expr:
        i = ScratchVar(TealType.uint64)
        length = ScratchVar(TealType.uint64)
        return For(
            Seq(length.store(self.length()), i.store(Int(0))),
            i.load() < length.load(),
            i.store(i.load() + Int(1)),
        ).Do(self.__getitem__(i.load()).use(lambda value: action(value, i.load())))

    def map(self, mapFn: Callable[[T, Expr, T], Expr]) -> Expr:
        # This implementation of map is functional (though I haven't tested it), but it returns the
        # encoded value of an Array. Instead, we actually want it to return an instance of an Array
        # Type -- to do this, we might want to generalize the ArrayElement and TupleElement interface
        # (meaning you could store the return value into a compatible Type object, or call .use on it
        # directly to immediately to use it)
        i = ScratchVar(TealType.uint64)
        length = ScratchVar(TealType.uint64)
        mappedArray = ScratchVar(TealType.bytes)
        mappedArrayIndex = ScratchVar(TealType.uint64)
        mappedValue = self._valueType.new_instance()

        initMappedArray = Seq(mappedArray.store(Bytes("")))
        addMappedValueToArray = Seq(
            mappedArray.store(Concat(mappedArray.load(), mappedValue.encode()))
        )

        if self._props.has_offsets:
            initMappedArray = Seq(
                mappedArrayIndex.store(Int(0)),
                # allocate space for header
                mappedArray.store(BytesZero(length.load() * Int(self._props.stride))),
            )

            newPointer = Uint16()

            # update new element in header
            addMappedValueToArray = Seq(
                mappedArray.store(
                    Concat(
                        Extract(
                            mappedArray.load(),
                            mappedArrayIndex.load(),
                            Int(self._props.stride),
                        ),
                        Seq(
                            mappedArrayIndex.store(
                                mappedArrayIndex.load() + Int(self._props.stride)
                            ),
                            newPointer.set(Len(mappedArray.load())),
                            newPointer.encode(),
                        ),
                        Suffix(mappedArray.load(), mappedArrayIndex.load()),
                        mappedValue.encode(),
                    )
                ),
            )

        return Seq(
            length.store(self.length()),
            initMappedArray,  # allocate space for bounds
            For(
                i.store(Int(0)), i.load() < length.load(), i.store(i.load() + Int(1))
            ).Do(
                Seq(
                    self.__getitem__(i.load()).use(
                        lambda value: mapFn(value, i.load(), mappedValue)
                    ),
                    addMappedValueToArray,
                )
            ),
            mappedArray.load(),
        )


Array.__module__ = "pyteal"

# until something like https://github.com/python/mypy/issues/3345 is added, we can't make the size of the array a generic parameter
class StaticArray(Array[T]):
    def __init__(self, valueType: T, length: int) -> None:
        super().__init__(valueType, length)

    def has_same_type_as(self, other: Type) -> bool:
        return (
            type(other) is StaticArray
            and self._valueType.has_same_type_as(other._valueType)
            and self.length_static() == other.length_static()
        )

    def new_instance(self) -> "StaticArray":
        return StaticArray(self._valueType, self.length_static())

    def is_dynamic(self) -> bool:
        return self._valueType.is_dynamic()

    def byte_length_static(self) -> int:
        if self.is_dynamic():
            raise ValueError("Type is dynamic")
        # TODO: bool support
        return self.length_static() * self._valueType.byte_length_static()

    def set(self, values: Sequence[T]) -> Expr:
        if self.length_static() != len(values):
            raise ValueError(
                "Incorrect length for values. Expected {}, got {}".format(
                    self.length_static(), len(values)
                )
            )
        return super().set(values)

    def length_static(self) -> int:
        return cast(int, self._props.static_length)

    def length(self) -> Expr:
        return Int(self.length_static())


StaticArray.__module__ = "pyteal"


class DynamicArray(Array[T]):
    def __init__(self, valueType: T) -> None:
        super().__init__(valueType, None)

    def has_same_type_as(self, other: Type) -> bool:
        return type(other) is DynamicArray and self._valueType.has_same_type_as(
            other._valueType
        )

    def new_instance(self) -> "DynamicArray":
        return DynamicArray(self._valueType)

    def is_dynamic(self) -> bool:
        return True

    def byte_length_static(self) -> int:
        raise ValueError("Type is dynamic")

    def length(self) -> Expr:
        return arrayLength(self.encode(), self._props)


DynamicArray.__module__ = "pyteal"


class ArrayElement(Generic[T]):
    def __init__(self, parent: Array[T], index: Expr) -> None:
        self.parent = parent
        self.index = index

    def store_into(self, output: T) -> Expr:
        return indexArray(
            self.parent._valueType,
            self.parent.encode(),
            self.index,
            output,
            self.parent._props,
        )

    def use(self, action: Callable[[T], Expr]) -> Expr:
        newInstance = self.parent._valueType.new_instance()
        return Seq(self.store_into(newInstance), action(newInstance))


ArrayElement.__module__ = "pyteal"
