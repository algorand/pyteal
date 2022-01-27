from typing import (
    Callable,
    List,
    Optional,
    Union,
    Sequence,
    NamedTuple,
)

from ...compiler import CompileOptions
from ..scratchvar import ScratchVar
from ..naryexpr import Concat, Add
from ..substring import Substring
from ..for_ import For
from ..if_ import If

from .type import ABIType, ABIValue
from .bytes import *
from .uint import *

# T = TypeVar("T", bound=ABIType)


def encodeTuple(values: Sequence[ABIValue]) -> Expr:
    heads: List[Expr] = []
    head_length_static: int = 0

    for elem in values:
        if elem.get_type().is_dynamic():
            head_length_static += 2
            heads.append(Bytes(b"\x00\x00"))
        else:
            # TODO: bool support
            head_length_static += elem.get_type().byte_length_static()
            heads.append(elem.encode())

    tails: List[ScratchVar] = []

    # tail_length_dynamic = ScratchVar(TealType.uint64)
    # tail_holder = ScratchVar(TealType.bytes)

    # TODO
    # tail_length_dynamic.store(Int(head_length_static))

    for i, elem in enumerate(values):
        if elem.get_type().is_dynamic():
            elemTail = ScratchVar(TealType.bytes)
            offset = Add(Int(head_length_static), *[Len(tail.load()) for tail in tails])

            heads[i] = Seq(elemTail.store(elem.encode()), Uint16(offset).encode())
            tails.append(elemTail)

    return Concat(*heads, *[tail.load() for tail in tails])


def indexTuple(valueTypes: Sequence[ABIType], encoded: Expr, index: int) -> ABIValue:
    if not (0 <= index < len(valueTypes)):
        raise ValueError("Index outside of range")

    offset = 0
    for typeBefore in valueTypes[:index]:
        if typeBefore.is_dynamic():
            offset += 2
        else:
            offset += typeBefore.byte_length_static()

    valueType = valueTypes[index]
    if valueType.is_dynamic():
        startIndex = ExtractUint16(encoded, Int(offset))
        if index + 1 == len(valueType):
            length = Len(encoded) - startIndex
        else:
            length = ExtractUint16(encoded, Int(offset + 2)) - startIndex
    else:
        startIndex = Int(offset)
        length = Int(valueType.byte_length_static())

    return valueType.decode(encoded, startIndex, length)


class ArrayData(NamedTuple):
    has_length_prefix: bool
    has_offsets: bool
    stride: int
    encoded: Expr


def createArray(
    elementType: ABIType, values: Sequence[ABIValue], dynamic_length: bool
) -> ArrayData:
    if not dynamic_length:
        encoded = encodeTuple(values)

        if not elementType.is_dynamic():
            return ArrayData(
                has_length_prefix=False,
                has_offsets=False,
                stride=elementType.byte_length_static(),  # TODO: bool support
                encoded=encoded,
            )

        return ArrayData(
            has_length_prefix=False, has_offsets=True, stride=2, encoded=encoded
        )

    length_prefix = Uint16(len(values)).encode()
    data = createArray(elementType, values, False)

    return ArrayData(
        has_length_prefix=True,
        has_offsets=data.has_offsets,
        stride=data.stride,
        encoded=Concat(length_prefix, data.encoded),
    )


def arrayLength(data: ArrayData) -> Expr:
    assert data.has_length_prefix

    return Uint16Type().decode(data.encoded, Int(0), Int(2)).value()


def decodeArray(
    elementType: ABIType,
    dynamic_length: bool,
    encoded: Expr,
    offset: Expr,
    length: Expr,
) -> ArrayData:
    encodedSubstring = Extract(encoded, offset, length)

    if not elementType.is_dynamic():
        return ArrayData(
            has_length_prefix=dynamic_length,
            has_offsets=False,
            stride=elementType.byte_length_static(),
            encoded=encodedSubstring,
        )

    return ArrayData(
        has_length_prefix=dynamic_length,
        has_offsets=True,
        stride=2,
        encoded=encodedSubstring,
    )


def indexArray(
    valueType: ABIType, data: ArrayData, index: Expr, length: int = None
) -> ABIValue:
    offsetIndex = Int(data.stride) * index

    if data.has_length_prefix:
        assert length is None
        lengthExpr = Uint16Type().decode(data.encoded, Int(0), Int(2))
        offsetIndex = offsetIndex + Int(2)
    else:
        assert length is not None
        lengthExpr = Int(length)

    if data.has_offsets:
        # TODO: startIndex is an index to data.offsets + data.values, but this code treats it as an
        # index to just data.values -- I don't think there's a good reason to separate the two anymore...
        valueStartRelative = ExtractUint16(data.encoded, offsetIndex)
        if data.has_length_prefix:
            valueStart = valueStartRelative + Int(2)
        else:
            valueStart = valueStartRelative
        valueLength = (
            If(index + Int(1) == lengthExpr)
            .Then(lengthExpr * Int(data.stride) - valueStartRelative)
            .Else(
                ExtractUint16(data.encoded, offsetIndex + Int(2)) - valueStartRelative
            )
        )
    else:
        valueStart = offsetIndex
        valueLength = Int(data.stride)

    return valueType.decode(data.encoded, valueStart, valueLength)


class ABITupleType(ABIType):
    def __init__(self, elementTypes: Sequence[ABIType]) -> None:
        super().__init__()
        self.elementTypes = list(elementTypes)

    def is_dynamic(self) -> bool:
        return any(e.is_dynamic() for e in self.elementTypes)

    def byte_length_static(self) -> int:
        if self.is_dynamic():
            raise ValueError("Type is dynamic")
        # TODO: bool support
        return sum(e.byte_length_static() for e in self.elementTypes)

    def decode(self, encoded: Expr, offset: Expr, length: Expr) -> "ABITuple":
        return ABITuple(type=self, _rawValues=Extract(encoded, offset, length))


ABITupleType.__module__ = "pyteal"


class ABITuple(ABIValue):
    def __init__(
        self,
        *,
        values: Sequence[ABIValue] = None,
        type: ABITupleType = None,
        _rawValues: Expr = None
    ) -> None:
        # TODO: argument checking
        if type is None:
            type = ABITupleType([v.get_type() for v in values])
        super().__init__(type)
        if _rawValues is not None:
            self.value = _rawValues
        else:
            self.value = encodeTuple(values)

    def byte_length(self) -> Expr:
        return Len(self.value)

    def encode(self) -> Expr:
        return self.value

    def length_static(self) -> int:
        return len(self.type.elementTypes)

    def length(self) -> Uint64:
        return Uint64(self.length_static())

    def __getitem__(self, index: int) -> ABIValue:
        return indexTuple(self.type.elementTypes, self.value, index)


ABITuple.__module__ = "pyteal"


class ABIFixedArrayType(ABIType):
    def __init__(self, elementType: ABIType, length: int) -> None:
        super().__init__()
        self.elementType = elementType
        self.length = length

    def is_dynamic(self) -> bool:
        return self.elementType.is_dynamic()

    def byte_length_static(self) -> int:
        if self.is_dynamic():
            raise ValueError("Type is dynamic")
        # TODO: bool support
        return self.length * self.elementType.byte_length_static()

    def decode(self, encoded: Expr, offset: Expr, length: Expr) -> "ABIFixedArray":
        data = decodeArray(self.elementType, False, encoded, offset, length)
        return ABIFixedArray(type=self, _rawData=data)


ABIFixedArrayType.__module__ = "pyteal"


class ABIFixedArray(ABIValue):
    def __init__(
        self,
        *,
        values: Sequence[ABIValue],
        type: ABIFixedArrayType = None,
        _rawData: ArrayData
    ) -> None:
        # TODO: argument checking
        if type is None:
            type = ABIFixedArrayType(values[0].get_type(), len(values))
            # TODO: check all values conform to elementType
        super().__init__(type)
        if _rawData is not None:
            self.data = _rawData
        else:
            self.data = createArray(type.elementType, values, False)

    def byte_length(self) -> Expr:
        if not self.type.is_dynamic():
            return Int(self.type.byte_length_static())
        return Len(self.data.encoded)

    def encode(self) -> Expr:
        return self.data.encoded

    def length_static(self) -> int:
        return self.type.length

    def length(self) -> Expr:
        return Int(self.length_static())

    def __getitem__(self, index: Union[int, Expr]) -> ABIValue:
        if type(index) is int:
            index = Int(index)
        return indexArray(self.type.elementType, self.data, index, self.length_static())

    def forEach(self, action: Callable[[ABIValue, Expr], Expr]) -> Expr:
        i = ScratchVar(TealType.uint64)
        return For(
            i.store(Int(0)), i.load() < self.length(), i.store(i.load() + Int(1))
        ).Do(action(self.__getitem__(i.load()), i.load()))


ABIFixedArray.__module__ = "pyteal"


class ABIDynamicArrayType(ABIType):
    def __init__(self, elementType: ABIType) -> None:
        super().__init__()
        self.elementType = elementType

    def is_dynamic(self) -> bool:
        return True

    def byte_length_static(self) -> int:
        raise ValueError("Type is dynamic")

    def decode(self, encoded: Expr, offset: Expr, length: Expr) -> "ABIDynamicArray":
        data = decodeArray(self.elementType, True, encoded, offset, length)
        return ABIDynamicArray(type=self, _rawData=data)


ABIDynamicArrayType.__module__ = "pyteal"


class ABIDynamicArray(ABIValue):
    def __init__(
        self,
        *,
        values: Sequence[ABIValue] = None,
        type: ABIDynamicArrayType = None,
        _rawData: ArrayData = None
    ) -> None:
        # TODO: argument checking
        if type is None:
            type = ABIDynamicArrayType(values[0].get_type())
            # TODO: check all values conform to elementType
        super().__init__(type)
        if _rawData is not None:
            self.data = _rawData
        else:
            self.data = createArray(type.elementType, values, True)

    def length(self) -> Expr:
        return arrayLength(self.data)

    def byte_length(self) -> Expr:
        return Len(self.data.encoded)

    def encode(self) -> Expr:
        return self.data.encoded

    def __getitem__(self, index: Union[int, Expr]) -> ABIValue:
        if type(index) is int:
            index = Int(index)
        return indexArray(self.type.elementType, self.data, index)

    def forEach(self, action: Callable[[ABIValue, Expr], Expr]) -> Expr:
        i = ScratchVar(TealType.uint64)
        return For(
            i.store(Int(0)), i.load() < self.length(), i.store(i.load() + Int(1))
        ).Do(action(self.__getitem__(i.load()), i.load()))


ABIDynamicArray.__module__ = "pyteal"
