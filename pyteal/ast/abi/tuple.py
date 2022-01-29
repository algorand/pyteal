from typing import (
    Callable,
    List,
    Sequence,
    Optional,
    cast,
)

from ...types import TealType
from ..expr import Expr
from ..seq import Seq
from ..int import Int
from ..unaryexpr import Len
from ..binaryexpr import ExtractUint16
from ..naryexpr import Add, Concat
from ..substring import Extract
from ..scratchvar import ScratchVar

from .type import Type
from .uint import Uint16


def encodeTuple(values: Sequence[Type]) -> Expr:
    heads: List[Optional[Expr]] = []
    head_length_static: int = 0

    for elem in values:
        if elem.is_dynamic():
            head_length_static += 2
            heads.append(None)  # a placeholder
        else:
            # TODO: bool support
            head_length_static += elem.byte_length_static()
            heads.append(elem.encode())

    tails: List[ScratchVar] = []

    # tail_length_dynamic = ScratchVar(TealType.uint64)
    # tail_holder = ScratchVar(TealType.bytes)

    # TODO
    # tail_length_dynamic.store(Int(head_length_static))

    for i, elem in enumerate(values):
        if elem.is_dynamic():
            elemTail = ScratchVar(TealType.bytes)
            offset = Uint16()

            heads[i] = Seq(
                elemTail.store(elem.encode()),
                offset.set(
                    Add(Int(head_length_static), *[Len(tail.load()) for tail in tails])
                ),
                offset.encode(),
            )
            tails.append(elemTail)

    return Concat(*cast(List[Expr], heads), *[tail.load() for tail in tails])


def indexTuple(
    valueTypes: Sequence[Type], encoded: Expr, index: int, output: Type
) -> Expr:
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
        if index + 1 == len(valueTypes):
            length = Len(encoded) - startIndex
        else:
            length = ExtractUint16(encoded, Int(offset + 2)) - startIndex
    else:
        startIndex = Int(offset)
        length = Int(valueType.byte_length_static())

    if not valueType.has_same_type_as(output):
        raise TypeError("Output type does not match value type")

    return output.decode(encoded, startIndex, length)


class Tuple(Type):
    def __init__(self, *valueTypes: Type) -> None:
        super().__init__(TealType.bytes)
        self.valueTypes = list(valueTypes)

    def has_same_type_as(self, other: Type) -> bool:
        return (
            type(other) is Tuple
            and len(self.valueTypes) == len(other.valueTypes)
            and all(
                self.valueTypes[i].has_same_type_as(other.valueTypes[i])
                for i in range(len(self.valueTypes))
            )
        )

    def new_instance(self) -> "Tuple":
        return Tuple(*self.valueTypes)

    def is_dynamic(self) -> bool:
        return any(valueType.is_dynamic() for valueType in self.valueTypes)

    def byte_length_static(self) -> int:
        if self.is_dynamic():
            raise ValueError("Type is dynamic")
        # TODO: bool support
        return sum(valueType.byte_length_static() for valueType in self.valueTypes)

    def decode(self, encoded: Expr, offset: Expr, length: Expr) -> Expr:
        return self.stored_value.store(Extract(encoded, offset, length))

    def set(self, *values: Type) -> Expr:
        if len(self.valueTypes) != len(values):
            raise ValueError(
                "Incorrect length for values. Expected {}, got {}".format(
                    len(self.valueTypes), len(values)
                )
            )
        if not all(
            self.valueTypes[i].has_same_type_as(values[i])
            for i in range(len(self.valueTypes))
        ):
            raise ValueError(
                "Input values do not match type"
            )  # TODO: add more to error message
        return self.stored_value.store(encodeTuple(values))

    def encode(self) -> Expr:
        return self.stored_value.load()

    def length_static(self) -> int:
        return len(self.valueTypes)

    def length(self) -> Expr:
        return Int(self.length_static())

    def __getitem__(self, index: int) -> "TupleElement":
        return TupleElement(self, index)


Tuple.__module__ = "pyteal"


class TupleElement:
    def __init__(self, parent: Tuple, index: int) -> None:
        self.parent = parent
        self.index = index

    def store_into(self, output: Type) -> Expr:
        return indexTuple(
            self.parent.valueTypes, self.parent.encode(), self.index, output
        )

    def use(self, action: Callable[[Type], Expr]) -> Expr:
        valueType = self.parent.valueTypes[self.index]
        newInstance = valueType.new_instance()
        return Seq(
            self.store_into(newInstance),
            action(newInstance),
        )


TupleElement.__module__ = "pyteal"
