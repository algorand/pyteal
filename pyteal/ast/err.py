from ..types import TealType
from ..ir import TealOp, Op
from .leafexpr import LeafExpr

class Err(LeafExpr):
    """Expression that causes the program to immediately fail when executed."""

    def __init__(self):
        pass

    def __teal__(self):
        return [TealOp(Op.err)]

    def __str__(self):
        return "(err)"

    def type_of(self):
        return TealType.none

Err.__module__ = "pyteal"
