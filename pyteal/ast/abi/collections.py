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
    offsets: Optional[Expr]
    offset_stride: int
    values: Expr


def createArray(elementType: ABIType, values: Sequence[ABIValue]) -> ArrayData:
    if not elementType.is_dynamic():
        # all values will encode to the same length, no need to keep offsets
        return ArrayData(
            offsets=None,
            offset_stride=elementType.byte_length_static(),
            values=Concat(*[value.encode() for value in values]),
        )

    encodedValues = Concat(*[value.encode() for value in values])

    offsets = Bytes("")
    current_offset = ScratchVar(TealType.uint64)

    for i, value in enumerate(values):
        tmp = ScratchVar(TealType.uint64)

        if i == 0:
            offsets = Seq(
                tmp.store(value.byte_length()),
                current_offset.store(tmp.load()),
                Uint16(tmp.load()).encode(),
            )
            continue

        next_offset = current_offset.load() + tmp.load()

        offsets = Seq(
            tmp.store(value.byte_length()),
            current_offset.store(next_offset),
            Concat(encodedValues, Uint16(next_offset).encode()),
        )

    return ArrayData(
        offsets=offsets,
        offset_stride=Uint16Type.byte_length_static(),
        values=Concat(*encodedValues),
    )


def arrayLength(data: ArrayData) -> Expr:
    if data.offsets is None:
        return Len(data.values) / Int(data.offset_stride)

    return Len(data.offsets) / Int(data.offset_stride)


def encodedArrayLength(data: ArrayData, dynamic_length: bool) -> Expr:
    if not dynamic_length:
        if data.offsets is None:
            return Len(data.values)

        return Len(data.offsets) + Len(data.values)

    return Int(2) + encodedArrayLength(data, False)


def encodeArray(data: ArrayData, dynamic_length: bool) -> Expr:
    if not dynamic_length:
        if data.offsets is None:
            return data.values

        return Concat(data.offsets, data.values)

    return Concat(
        Uint16(arrayLength(data)).encode(),
        encodeArray(data, False),
    )


def decodeStaticArray(
    elementType: ABIType, size: Expr, encoded: Expr, offset: Expr, length: Expr
) -> ArrayData:
    if elementType.is_dynamic():
        stride = 2
        offsets_start = ExtractUint16(encoded, offset)
        offsets_length = Int(stride) * size
        offsets = Extract(encoded, offset + offsets_start, offsets_length)
        values = Extract(
            encoded, offset + offsets_start + offsets_length, length - offsets_length
        )
    else:
        stride = elementType.byte_length_static()
        offsets = None
        values = Extract(encoded, offset, length)

    return ArrayData(offsets=offsets, offset_stride=stride, values=values)


def decodeDynamicArray(
    elementType: ABIType, encoded: Expr, offset: Expr, length: Expr
) -> ArrayData:
    size = ExtractUint16(encoded, offset, Int(2))
    return decodeStaticArray(
        elementType, size, encoded, offset + Int(2), length - Int(2)
    )


def indexArray(valueType: ABIType, data: ArrayData, index: Expr) -> ABIValue:
    offsetIndex = Int(data.offset_stride) * index

    if data.offsets is not None:
        startIndex = ExtractUint16(data.offsets, offsetIndex)
        length = (
            If((index + Int(1)) * Int(data.offset_stride) == Len(data.offsets))
            .Then(Len(data.offsets) - startIndex)
            .Else(ExtractUint16(data.offsets, offsetIndex + Int(2)) - startIndex)
        )
    else:
        startIndex = offsetIndex
        length = Int(data.offset_stride)

    return valueType.decode(data.values, startIndex, length)


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
        data = decodeStaticArray(
            self.elementType, Int(self.length), encoded, offset, length
        )
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
            self.data = createArray(type.elementType, values)

    def byte_length(self) -> Expr:
        return encodedArrayLength(self.data)

    def encode(self) -> Expr:
        return encodeArray(self.data, False)

    def length_static(self) -> int:
        return self.length

    def length(self) -> Expr:
        return Int(self.length_static())

    def __getitem__(self, index: Union[int, Expr]) -> ABIValue:
        if type(index) is int:
            index = Int(index)
        return indexArray(self.type.elementType, self.data, index)

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
        raise NotImplementedError


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
            self.data = createArray(type.elementType, values)

    def length(self) -> Expr:
        return arrayLength(self.data)

    def byte_length(self) -> Expr:
        return encodedArrayLength(self.data, True)

    def encode(self) -> Expr:
        return encodeArray(self.data, True)

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
