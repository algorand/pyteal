from typing import Union, cast, Sequence

from ...types import TealType
from ..expr import Expr
from ..seq import Seq
from ..assert_ import Assert
from ..int import Int
from ..bytes import Bytes
from ..binaryexpr import GetBit
from ..ternaryexpr import SetBit
from .type import Type
from .uint import NUM_BITS_IN_BYTE


class Bool(Type):
    def __init__(self) -> None:
        super().__init__(TealType.uint64)

    def new_instance(self) -> "Bool":
        return Bool()

    def has_same_type_as(self, other: Type) -> bool:
        return type(other) is Bool

    def is_dynamic(self) -> bool:
        return False

    def byte_length_static(self) -> int:
        # Not completely accurate since up to 8 consecutive bools will fit into a single byte
        return 1

    def get(self) -> Expr:
        return self.stored_value.load()

    def set(self, value: Union[bool, Expr, "Bool"]) -> Expr:
        checked = False
        if type(value) is bool:
            value = Int(1 if value else 0)
            checked = True

        if type(value) is Bool:
            value = value.get()
            checked = True

        if checked:
            return self.stored_value.store(cast(Expr, value))

        return Seq(
            self.stored_value.store(cast(Expr, value)),
            Assert(self.stored_value.load() < Int(2)),
        )

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        if startIndex is None:
            startIndex = Int(0)
        return self.decodeBit(encoded, startIndex * Int(NUM_BITS_IN_BYTE))

    def decodeBit(self, encoded, bit: Expr) -> Expr:
        return self.stored_value.store(GetBit(encoded, bit))

    def encode(self) -> Expr:
        return SetBit(Bytes(b"\x00"), Int(0), self.get())

    def __str__(self) -> str:
        return "bool"


def boolAwareStaticByteLength(types: Sequence[Type]) -> int:
    length = 0
    ignoreNext = 0
    for i, t in enumerate(types):
        if ignoreNext > 0:
            ignoreNext -= 1
            continue
        if type(t) is Bool:
            numBools = consecutiveBoolNum(types, i)
            ignoreNext = numBools - 1
            length += boolSequenceLength(numBools)
            continue
        length += t.byte_length_static()
    return length


def consecutiveBoolNum(types: Sequence[Type], startIndex: int) -> int:
    numConsecutiveBools = 0
    for t in types[startIndex:]:
        if type(t) is not Bool:
            break
        numConsecutiveBools += 1
    return numConsecutiveBools


def boolSequenceLength(num_bools: int) -> int:
    return (num_bools + NUM_BITS_IN_BYTE - 1) // NUM_BITS_IN_BYTE


def encodeBoolSequence(values: Sequence[Bool]) -> Expr:
    length = boolSequenceLength(len(values))
    expr: Expr = Bytes(b"\x00" * length)

    for i, value in enumerate(values):
        expr = SetBit(expr, Int(i), value.get())

    return expr
