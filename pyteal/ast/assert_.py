from ..types import TealType, require_type
from ..ir import TealOp, Op, TealSimpleBlock, TealConditionalBlock
from .expr import Expr

class Assert(Expr):
    """A control flow expression to verify that a condition is true."""

    def __init__(self, cond: Expr) -> None:
        """Create an assert statement that raises an error if the condition is false.

        Args:
            cond: The condition to check. Must evaluate to a uint64.
        """
        super().__init__()
        require_type(cond.type_of(), TealType.uint64)
        self.cond = cond
    
    def __teal__(self):
        condStart, condEnd = self.cond.__teal__()

        end = TealSimpleBlock([])
        errBlock = TealSimpleBlock([TealOp(self, Op.err)])

        branchBlock = TealConditionalBlock([])
        branchBlock.setTrueBlock(end)
        branchBlock.setFalseBlock(errBlock)

        condEnd.setNextBlock(branchBlock)

        return condStart, end

    def __str__(self):
        return "(Assert {})".format(self.cond)

    def type_of(self):
        return TealType.none

Assert.__module__ = "pyteal"
