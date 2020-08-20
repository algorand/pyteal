from ..types import TealType, valid_address
from ..ir import TealOp, Op
from .leafexpr import LeafExpr

class Addr(LeafExpr):
    """An expression that represents an Algorand address."""

    def __init__(self, address: str) -> None:
        """Create a new Addr expression.

        Args:
            address: A string containing a valid base32 Algorand address
        """
        valid_address(address)
        self.address = address

    def __teal__(self):
        return [TealOp(Op.addr, self.address)]

    def __str__(self):
        return "(address: {})".format(self.address)

    def type_of(self):
        return TealType.bytes

Addr.__module__ = "pyteal"
