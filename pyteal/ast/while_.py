from typing import TYPE_CHECKING, Optional

from ..errors import TealCompileError
from ..types import TealType, require_type
from ..ir import TealSimpleBlock, TealConditionalBlock
from .expr import Expr
from .seq import Seq

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class While(Expr):
    """While expression."""

    def __init__(self, cond: Expr) -> None:
        """Create a new While expression.

        When this While expression is executed, the condition will be evaluated, and if it produces a
        true value, doBlock will be executed and return to the start of the expression execution.
        Otherwise, no branch will be executed.

        Args:
            cond: The condition to check. Must evaluate to uint64.
        """
        super().__init__()
        require_type(cond.type_of(), TealType.uint64)

        self.cond = cond
        self.doBlock: Optional[Expr] = None

    def __teal__(self, options: "CompileOptions"):
        if self.doBlock is None:
            raise TealCompileError("While expression must have a doBlock", self)

        breakBlocks = options.breakBlocks
        continueBlocks = options.continueBlocks
        prevLoop = options.currentLoop

        options.breakBlocks = []
        options.continueBlocks = []
        options.currentLoop = self

        condStart, condEnd = self.cond.__teal__(options)
        doStart, doEnd = self.doBlock.__teal__(options)
        end = TealSimpleBlock([])

        for block in options.breakBlocks:
            block.setNextBlock(end)

        for block in options.continueBlocks:
            block.setNextBlock(doStart)

        options.breakBlocks = breakBlocks
        options.continueBlocks = continueBlocks
        options.currentLoop = prevLoop

        doEnd.setNextBlock(condStart)

        branchBlock = TealConditionalBlock([])
        branchBlock.setTrueBlock(doStart)
        branchBlock.setFalseBlock(end)

        condEnd.setNextBlock(branchBlock)

        return condStart, end

    def __str__(self):
        if self.doBlock is None:
            raise TealCompileError("While expression must have a doBlock", self)

        return "(While {} {})".format(self.cond, self.doBlock)

    def type_of(self):
        if self.doBlock is None:
            raise TealCompileError("While expression must have a doBlock", self)
        return TealType.none

    def Do(self, doBlock: Expr):
        if self.doBlock is not None:
            raise TealCompileError("While expression already has a doBlock", self)
        require_type(doBlock.type_of(), TealType.none)
        self.doBlock = doBlock
        return self


While.__module__ = "pyteal"
