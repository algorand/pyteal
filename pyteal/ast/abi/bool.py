from typing import TypeVar, Union, cast, Sequence, Callable, Type as PyType

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
    @classmethod
    def has_same_type_as(cls, other: Union[PyType[Type], Type]) -> bool:
        return other is Bool or type(other) is Bool

    @classmethod
    def is_dynamic(cls) -> bool:
        return False

    @classmethod
    def byte_length_static(cls) -> int:
        # Not completely accurate since up to 8 consecutive bools will fit into a single byte
        return 1

    @classmethod
    def storage_type(cls) -> TealType:
        return TealType.uint64

    @classmethod
    def __str__(cls) -> str:
        return "bool"

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

    def decodeBit(self, encoded, bitIndex: Expr) -> Expr:
        return self.stored_value.store(GetBit(encoded, bitIndex))

    def encode(self) -> Expr:
        return SetBit(Bytes(b"\x00"), Int(0), self.get())


def boolAwareStaticByteLength(types: Sequence[PyType[Type]]) -> int:
    length = 0
    ignoreNext = 0
    for i, t in enumerate(types):
        if ignoreNext > 0:
            ignoreNext -= 1
            continue
        if t is Bool:
            numBools = consecutiveBoolTypeNum(types, i)
            ignoreNext = numBools - 1
            length += boolSequenceLength(numBools)
            continue
        length += t.byte_length_static()
    return length


T = TypeVar("T")


def consecutiveThingNum(
    things: Sequence[T], startIndex: int, condition: Callable[[T], bool]
) -> int:
    numConsecutiveThings = 0
    for t in things[startIndex:]:
        if not condition(t):
            break
        numConsecutiveThings += 1
    return numConsecutiveThings


def consecutiveBoolTypeNum(types: Sequence[PyType[Type]], startIndex: int) -> int:
    if len(types) != 0 and not issubclass(types[0], Type):
        raise TypeError("Sequence of types expected")
    return consecutiveThingNum(types, startIndex, lambda t: t is Bool)


def consecutiveBoolNum(values: Sequence[Type], startIndex: int) -> int:
    if len(values) != 0 and not isinstance(values[0], Type):
        raise TypeError("Sequence of types expected")
    return consecutiveThingNum(values, startIndex, lambda t: type(t) is Bool)


def boolSequenceLength(num_bools: int) -> int:
    return (num_bools + NUM_BITS_IN_BYTE - 1) // NUM_BITS_IN_BYTE


def encodeBoolSequence(values: Sequence[Bool]) -> Expr:
    length = boolSequenceLength(len(values))
    expr: Expr = Bytes(b"\x00" * length)

    for i, value in enumerate(values):
        expr = SetBit(expr, Int(i), value.get())

    return expr
