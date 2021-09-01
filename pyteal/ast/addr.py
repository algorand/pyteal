from typing import TYPE_CHECKING

from ..types import TealType, valid_address
from ..ir import TealOp, Op, TealBlock
from .leafexpr import LeafExpr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class Addr(LeafExpr):
    """An expression that represents an Algorand address."""

    def __init__(self, address: str) -> None:
        """Create a new Addr expression.

        Args:
            address: A string containing a valid base32 Algorand address
        """
        super().__init__()
        valid_address(address)
        self.address = address

    def __teal__(self, options: "CompileOptions"):
        op = TealOp(self, Op.addr, self.address)
        return TealBlock.FromOp(options, op)

    def __str__(self):
        return "(address: {})".format(self.address)

    def type_of(self):
        return TealType.bytes


Addr.__module__ = "pyteal"
