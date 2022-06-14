from typing import TypeVar, Union, cast, Sequence, Callable

from pyteal.types import TealType
from pyteal.errors import TealInputError
from pyteal.ast.expr import Expr
from pyteal.ast.seq import Seq
from pyteal.ast.assert_ import Assert
from pyteal.ast.int import Int
from pyteal.ast.bytes import Bytes
from pyteal.ast.binaryexpr import GetBit
from pyteal.ast.ternaryexpr import SetBit
from pyteal.ast.abi.type import ComputedValue, TypeSpec, BaseType
from pyteal.ast.abi.uint import NUM_BITS_IN_BYTE


class BoolTypeSpec(TypeSpec):
    def new_instance(self) -> "Bool":
        return Bool()

    def annotation_type(self) -> "type[Bool]":
        return Bool

    def is_dynamic(self) -> bool:
        # Only accurate if this value is alone, since up to 8 consecutive bools will fit into a single byte
        return False

    def byte_length_static(self) -> int:
        return 1

    def storage_type(self) -> TealType:
        return TealType.uint64

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BoolTypeSpec)

    def __str__(self) -> str:
        return "bool"


BoolTypeSpec.__module__ = "pyteal"


class Bool(BaseType):
    def __init__(self) -> None:
        super().__init__(BoolTypeSpec())

    def get(self) -> Expr:
        return self.stored_value.load()

    def set(self, value: Union[bool, Expr, "Bool", ComputedValue["Bool"]]) -> Expr:
        if isinstance(value, ComputedValue):
            return self._set_with_computed_type(value)

        value = cast(Union[bool, Expr, "Bool"], value)

        checked = False
        if type(value) is bool:
            value = Int(1 if value else 0)
            checked = True

        if isinstance(value, BaseType):
            if value.type_spec() != self.type_spec():
                raise TealInputError(
                    "Cannot set type bool to {}".format(value.type_spec())
                )
            value = value.get()
            checked = True

        if checked:
            return self.stored_value.store(value)

        return Seq(
            self.stored_value.store(value),
            Assert(self.stored_value.load() < Int(2)),
        )

    def decode(
        self,
        encoded: Expr,
        *,
        start_index: Expr = None,
        end_index: Expr = None,
        length: Expr = None
    ) -> Expr:
        if start_index is None:
            start_index = Int(0)
        return self.decodeBit(encoded, start_index * Int(NUM_BITS_IN_BYTE))

    def decodeBit(self, encoded, bitIndex: Expr) -> Expr:
        return self.stored_value.store(GetBit(encoded, bitIndex))

    def encode(self) -> Expr:
        return SetBit(Bytes(b"\x00"), Int(0), self.get())


def boolAwareStaticByteLength(types: Sequence[TypeSpec]) -> int:
    length = 0
    ignoreNext = 0
    for i, t in enumerate(types):
        if ignoreNext > 0:
            ignoreNext -= 1
            continue
        if t == BoolTypeSpec():
            numBools = consecutiveBoolTypeSpecNum(types, i)
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


def consecutiveBoolTypeSpecNum(types: Sequence[TypeSpec], startIndex: int) -> int:
    if len(types) != 0 and not isinstance(types[0], TypeSpec):
        raise TypeError("Sequence of types expected")
    return consecutiveThingNum(types, startIndex, lambda t: t == BoolTypeSpec())


def consecutiveBoolInstanceNum(values: Sequence[BaseType], startIndex: int) -> int:
    if len(values) != 0 and not isinstance(values[0], BaseType):
        raise TypeError(
            "Sequence of types expected, but got {}".format(type(values[0]))
        )
    return consecutiveThingNum(
        values, startIndex, lambda t: t.type_spec() == BoolTypeSpec()
    )


def boolSequenceLength(num_bools: int) -> int:
    """Get the length in bytes of an encoding of `num_bools` consecutive booleans values."""
    return (num_bools + NUM_BITS_IN_BYTE - 1) // NUM_BITS_IN_BYTE


def encodeBoolSequence(values: Sequence[Bool]) -> Expr:
    """Encoding a sequences of boolean values into a byte string.

    Args:
        values: The values to encode. Each must be an instance of Bool.

    Returns:
        An expression which creates an encoded byte string with the input boolean values.
    """
    length = boolSequenceLength(len(values))
    expr: Expr = Bytes(b"\x00" * length)

    for i, value in enumerate(values):
        expr = SetBit(expr, Int(i), value.get())

    return expr
