from typing import (
    Callable,
    Union,
    Sequence,
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


T = TypeVar("T", bound=Type)


class Array(Type, Generic[T]):
    def __init__(self, valueType: T, staticLength: Optional[int]) -> None:
        super().__init__(TealType.bytes)
        self._valueType = valueType

        self._has_offsets = valueType.is_dynamic()
        if self._has_offsets:
            self._stride = 2
        else:
            self._stride = valueType.byte_length_static()
        self._static_length = staticLength

    def decode(self, encoded: Expr, offset: Expr, length: Expr) -> Expr:
        return self.stored_value.store(Extract(encoded, offset, length))

    def set(self, values: Sequence[T]) -> Expr:
        if not all(self._valueType.has_same_type_as(value) for value in values):
            raise ValueError(
                "Input values do not match type"
            )  # TODO: add more to error message

        encoded = encodeTuple(values)

        if self._static_length is None:
            length_tmp = Uint16()
            length_prefix = Seq(length_tmp.set(len(values)), length_tmp.encode())
            encoded = Concat(length_prefix, encoded)

        return self.stored_value.store(encoded)

    def encode(self) -> Expr:
        return self.stored_value.load()

    @abstractmethod
    def length(self) -> Expr:
        pass

    def __getitem__(
        self, index: Union[int, Expr], length: Expr = None
    ) -> "ArrayElement[T]":
        if type(index) is int:
            index = Int(index)
        return ArrayElement(self, cast(Expr, index), length)

    def forEach(self, action: Callable[[T, Expr], Expr]) -> Expr:
        i = ScratchVar(TealType.uint64)
        length = ScratchVar(TealType.uint64)
        return For(
            Seq(length.store(self.length()), i.store(Int(0))),
            i.load() < length.load(),
            i.store(i.load() + Int(1)),
        ).Do(
            self.__getitem__(i.load(), length=length.load()).use(
                lambda value: action(value, i.load())
            )
        )

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

        if self._has_offsets:
            initMappedArray = Seq(
                mappedArrayIndex.store(Int(0)),
                # allocate space for header
                mappedArray.store(BytesZero(length.load() * Int(self._stride))),
            )

            newPointer = Uint16()

            # update new element in header
            addMappedValueToArray = Seq(
                mappedArray.store(
                    Concat(
                        Extract(
                            mappedArray.load(),
                            mappedArrayIndex.load(),
                            Int(self._stride),
                        ),
                        Seq(
                            mappedArrayIndex.store(
                                mappedArrayIndex.load() + Int(self._stride)
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
                    self.__getitem__(i.load(), length=length.load()).use(
                        lambda value: mapFn(value, i.load(), mappedValue)
                    ),
                    addMappedValueToArray,
                )
            ),
            mappedArray.load(),
        )

    def __str__(self) -> str:
        return self._valueType.__str__() + (
            "[]"
            if self._props.static_length is None
            else "[{}]".format(self._props.static_length)
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
        return cast(int, self._static_length)

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
        output = Uint16()
        return Seq(
            output.decode(self.encode(), Int(0), Int(2)),
            output.get(),
        )


DynamicArray.__module__ = "pyteal"


class ArrayElement(Generic[T]):
    def __init__(self, array: Array[T], index: Expr, length: Expr = None) -> None:
        self.array = array
        self.index = index
        self.length = length

    def store_into(self, output: T) -> Expr:
        return self._compute(output)

    def use(self, action: Callable[[T], Expr]) -> Expr:
        newInstance = self.array._valueType.new_instance()
        return Seq(self.store_into(newInstance), action(newInstance))

    def _compute(self, output: T) -> Expr:
        offsetIndex = Int(self.array._stride) * self.index
        if self.array._static_length is None:
            offsetIndex = offsetIndex + Int(2)

        if self.length:
            arrayLength = self.length
        else:
            arrayLength = self.array.length()

        encodedArray = self.array.encode()

        if self.array._has_offsets:
            valueStartRelative = ExtractUint16(encodedArray, offsetIndex)
            if self.array._static_length is None:
                valueStart = valueStartRelative + Int(2)
            else:
                valueStart = valueStartRelative
            valueLength = (
                If(self.index + Int(1) == arrayLength)
                .Then(arrayLength * Int(self.array._stride) - valueStartRelative)
                .Else(
                    ExtractUint16(encodedArray, offsetIndex + Int(2))
                    - valueStartRelative
                )
            )
        else:
            valueStart = offsetIndex
            valueLength = Int(self.array._stride)

        if not self.array._valueType.has_same_type_as(output):
            raise TypeError("Output type does not match value type")

        return output.decode(encodedArray, valueStart, valueLength)


ArrayElement.__module__ = "pyteal"
