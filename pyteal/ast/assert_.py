from ..types import TealType, require_type
from ..ir import TealOp, Op, TealLabel
from ..util import new_label
from .expr import Expr

class Assert(Expr):
    """A control flow expression to verify that a condition is true."""

    def __init__(self, cond: Expr) -> None:
        """Create an assert statement that raises an error if the condition is false.

        Args:
            cond: The condition to check. Must evaluate to a uint64.
        """
        require_type(cond.type_of(), TealType.uint64)
        self.cond = cond
    
    def __teal__(self):
        end = new_label()
        teal = self.cond.__teal__()
        teal.append(TealOp(Op.bnz, end))
        teal.append(TealOp(Op.err))
        teal.append(TealLabel(end))

        return teal

    def __str__(self):
        return "(Assert {})".format(self.cond)

    def type_of(self):
        return TealType.none

Assert.__module__ = "pyteal"
