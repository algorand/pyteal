from typing import Union, TYPE_CHECKING

from ..types import TealType
from ..ir import TealOp, Op, TealBlock
from ..errors import TealInputError
from .leafexpr import LeafExpr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class Int(LeafExpr):
    """An expression that represents a uint64."""

    def __init__(self, value: int) -> None:
        """Create a new uint64.

        Args:
            value: The integer value this uint64 will represent. Must be a positive value less than
                2**64.
        """
        super().__init__()

        if type(value) is not int:
            raise TealInputError("invalid input type {} to Int".format(type(value)))
        elif value >= 0 and value < 2 ** 64:
            self.value = value
        else:
            raise TealInputError("Int {} is out of range".format(value))

    def __teal__(self, options: "CompileOptions"):
        op = TealOp(self, Op.int, self.value)
        return TealBlock.FromOp(options, op)

    def __str__(self):
        return "(Int: {})".format(self.value)

    def type_of(self):
        return TealType.uint64


Int.__module__ = "pyteal"


class EnumInt(LeafExpr):
    """An expression that represents uint64 enum values."""

    def __init__(self, name: str) -> None:
        """Create an expression to reference a uint64 enum value.

        Args:
            name: The name of the enum value.
        """
        super().__init__()
        self.name = name

    def __teal__(self, options: "CompileOptions"):
        op = TealOp(self, Op.int, self.name)
        return TealBlock.FromOp(options, op)

    def __str__(self):
        return "(IntEnum: {})".format(self.name)

    def type_of(self):
        return TealType.uint64


EnumInt.__module__ = "pyteal"
