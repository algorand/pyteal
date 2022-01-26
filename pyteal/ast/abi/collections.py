from typing import List, Union, Generic, Sequence, TypeVar, get_type_hints, cast

from ...compiler import CompileOptions
from ..scratchvar import ScratchVar
from ..naryexpr import Concat, Add
from ..substring import Substring
from ..for_ import For

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
    valueOffset = Int(offset)

    valueType = valueTypes[index]
    if valueType.is_dynamic():
        offset = ExtractUint16(encoded, valueOffset)

    return valueType.decode(encoded, valueOffset)


def indexArray(valueType: ABIType, encoded: Expr, index: Expr) -> ABIValue:
    if valueType.is_dynamic():
        stride = Int(2)
    else:
        stride = Int(valueType.byte_length_static())
    offset = stride * index

    if valueType.is_dynamic():
        offset = ExtractUint16(encoded, offset)

    return valueType.decode(encoded, offset)


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

    def decode(self, encoded: Expr, offset: Expr = None) -> "ABITupleType":
        raise NotImplementedError


ABITupleType.__module__ = "pyteal"


class ABITuple(ABIValue):
    def __init__(self, values: Sequence[ABIValue]) -> None:
        types = [v.get_type() for v in values]
        super().__init__(ABITupleType(types))
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

    def decode(self, encoded: Expr, offset: Expr = None) -> "ABIFixedArrayType":
        raise NotImplementedError


ABIFixedArrayType.__module__ = "pyteal"


class ABIFixedArray(ABIValue):
    def __init__(self, values: Sequence[ABIValue]) -> None:
        elementType = type(values[0])
        # TODO: check all values conform to elementType
        super().__init__(ABIFixedArrayType(elementType, len(values)))
        self.value = encodeTuple(values)
        self.length = len(values)

    def byte_length(self) -> Expr:
        return Len(self.value) + Int(2)

    def encode(self) -> Expr:
        return self.value

    def length_static(self) -> int:
        return self.length

    def length(self) -> Uint64:
        return Uint64(self.length_static())

    def __getitem__(self, index: Union[int, Expr]) -> ABIValue:
        if type(index) is int:
            index = Int(index)
        return indexArray(self.type.elementType, self.value, index)


ABIFixedArray.__module__ = "pyteal"


class ABIDynamicArrayType(ABIType):
    def __init__(self, elementType: ABIType) -> None:
        super().__init__()
        self.elementType = elementType

    def is_dynamic(self) -> bool:
        return True

    def byte_length_static(self) -> int:
        raise ValueError("Type is dynamic")

    def decode(self, encoded: Expr, offset: Expr = None) -> "ABIDynamicArrayType":
        raise NotImplementedError


ABIDynamicArrayType.__module__ = "pyteal"


class ABIDynamicArray(ABIValue):
    def __init__(
        self, values: Sequence[ABIValue] = None, elementType: ABIType = None
    ) -> None:
        if values is not None and len(values) != 0:
            elementType = values[0].get_type()
        # TODO: check all values conform to elementType
        super().__init__(ABIDynamicArrayType(elementType))
        self.value = encodeTuple(values)
        self.len = Uint16(len(values))

    def length(self) -> Uint16:
        return self.len

    def byte_length(self) -> Expr:
        return Int(2) + Len(self.value)

    def encode(self) -> Expr:
        return Concat(self.len.encode(), self.value)

    def __getitem__(self, index: Union[int, Expr]) -> ABIValue:
        if type(index) is int:
            index = Int(index)
        return indexArray(self.type.elementType, self.value, index)


ABIDynamicArray.__module__ = "pyteal"
