from typing import TYPE_CHECKING

from ..types import TealType, require_type
from ..ir import TealOp, Op, TealBlock, TealSimpleBlock, TealConditionalBlock
from .expr import Expr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class Assert(Expr):
    """A control flow expression to verify that a condition is true."""

    def __init__(self, cond: Expr) -> None:
        """Create an assert statement that raises an error if the condition is false.

        Args:
            cond: The condition to check. Must evaluate to a uint64.
        """
        super().__init__()
        require_type(cond, TealType.uint64)
        self.cond = cond

    def __teal__(self, options: "CompileOptions"):
        if options.version >= Op.assert_.min_version:
            # use assert op if available
            return TealBlock.FromOp(options, TealOp(self, Op.assert_), self.cond)

        # if assert op is not available, use branches and err
        condStart, condEnd = self.cond.__teal__(options)

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

    def has_return(self):
        return False


Assert.__module__ = "pyteal"
