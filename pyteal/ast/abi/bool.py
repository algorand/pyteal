from typing import TypeVar, Union, Sequence, Callable

from pyteal.types import TealType
from pyteal.errors import TealInputError
from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from pyteal.ast.bytes import Bytes
from pyteal.ast.unaryexpr import Not
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


BoolTypeSpec.__module__ = "pyteal.abi"


class Bool(BaseType):
    def __init__(self) -> None:
        super().__init__(BoolTypeSpec())

    def get(self) -> Expr:
        """Return the value held by this Bool as a PyTeal expression.

        If the held value is true, an expression that evaluates to 1 will be returned. Otherwise, an
        expression that evaluates to 0 will be returned. In either case, the expression will have the
        type TealType.uint64.
        """
        return self.stored_value.load()

    def set(self, value: Union[bool, Expr, "Bool", ComputedValue["Bool"]]) -> Expr:
        """Set the value of this Bool to the input value.

        The behavior of this method depends on the input argument type:

            * :code:`bool`: set the value to a Python boolean value.
            * :code:`Expr`: set the value to the result of a PyTeal expression, which must evaluate to a TealType.uint64. All values greater than 0 are considered true, while 0 is considered false.
            * :code:`Bool`: copy the value from another Bool.
            * :code:`ComputedValue[Bool]`: copy the value from a Bool produced by a ComputedValue.

        Args:
            value: The new value this Bool should take. This must follow the above constraints.

        Returns:
            An expression which stores the given value into this Bool.
        """
        if isinstance(value, ComputedValue):
            return self._set_with_computed_type(value)

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

        # Not(Not(value)) coerces all values greater than 0 to 1
        return self.stored_value.store(Not(Not(value)))

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
        return self.decode_bit(encoded, start_index * Int(NUM_BITS_IN_BYTE))

    def decode_bit(self, encoded, bit_index: Expr) -> Expr:
        return self.stored_value.store(GetBit(encoded, bit_index))

    def encode(self) -> Expr:
        return SetBit(Bytes(b"\x00"), Int(0), self.get())


Bool.__module__ = "pyteal.abi"


def _bool_aware_static_byte_length(types: Sequence[TypeSpec]) -> int:
    length = 0
    ignoreNext = 0
    for i, t in enumerate(types):
        if ignoreNext > 0:
            ignoreNext -= 1
            continue
        if t == BoolTypeSpec():
            numBools = _consecutive_bool_type_spec_num(types, i)
            ignoreNext = numBools - 1
            length += _bool_sequence_length(numBools)
            continue
        length += t.byte_length_static()
    return length


T = TypeVar("T")


def _consecutive_thing_num(
    things: Sequence[T], start_index: int, condition: Callable[[T], bool]
) -> int:
    numConsecutiveThings = 0
    for t in things[start_index:]:
        if not condition(t):
            break
        numConsecutiveThings += 1
    return numConsecutiveThings


def _consecutive_bool_type_spec_num(types: Sequence[TypeSpec], start_index: int) -> int:
    if len(types) != 0 and not isinstance(types[0], TypeSpec):
        raise TypeError("Sequence of types expected")
    return _consecutive_thing_num(types, start_index, lambda t: t == BoolTypeSpec())


def _consecutive_bool_instance_num(values: Sequence[BaseType], start_index: int) -> int:
    if len(values) != 0 and not isinstance(values[0], BaseType):
        raise TypeError(
            "Sequence of types expected, but got {}".format(type(values[0]))
        )
    return _consecutive_thing_num(
        values, start_index, lambda t: t.type_spec() == BoolTypeSpec()
    )


def _bool_sequence_length(num_bools: int) -> int:
    """Get the length in bytes of an encoding of `num_bools` consecutive booleans values."""
    return (num_bools + NUM_BITS_IN_BYTE - 1) // NUM_BITS_IN_BYTE


def _encode_bool_sequence(values: Sequence[Bool]) -> Expr:
    """Encoding a sequences of boolean values into a byte string.

    Args:
        values: The values to encode. Each must be an instance of Bool.

    Returns:
        An expression which creates an encoded byte string with the input boolean values.
    """
    length = _bool_sequence_length(len(values))
    expr: Expr = Bytes(b"\x00" * length)

    for i, value in enumerate(values):
        expr = SetBit(expr, Int(i), value.get())

    return expr
