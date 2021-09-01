from typing import TYPE_CHECKING, Optional

from ..types import TealType, require_type
from ..ir import TealSimpleBlock, TealConditionalBlock
from ..errors import TealCompileError
from .expr import Expr
from .seq import Seq
from .int import Int

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class For(Expr):
    """For expression."""

    def __init__(self, start: Expr, cond: Expr, step: Expr) -> None:
        """Create a new For expression.

        When this For expression is executed, the condition will be evaluated, and if it produces a
        true value, doBlock will be executed and return to the start of the expression execution.
        Otherwise, no branch will be executed.

        Args:
            start: Expression setting the variable's initial value
            cond: The condition to check. Must evaluate to uint64.
            step: Expression to update the variable's value.
        """
        super().__init__()
        require_type(cond.type_of(), TealType.uint64)
        require_type(start.type_of(), TealType.none)
        require_type(step.type_of(), TealType.none)

        self.start = start
        self.cond = cond
        self.step = step
        self.doBlock: Optional[Expr] = None

    def __teal__(self, options: "CompileOptions"):
        if self.doBlock is None:
            raise TealCompileError("For expression must have a doBlock", self)

        options.enterLoop()

        end = TealSimpleBlock([])
        start, startEnd = self.start.__teal__(options)
        condStart, condEnd = self.cond.__teal__(options)
        doStart, doEnd = self.doBlock.__teal__(options)

        stepStart, stepEnd = self.step.__teal__(options)
        stepEnd.setNextBlock(condStart)
        doEnd.setNextBlock(stepStart)

        branchBlock = TealConditionalBlock([])
        branchBlock.setTrueBlock(doStart)
        branchBlock.setFalseBlock(end)

        condEnd.setNextBlock(branchBlock)

        startEnd.setNextBlock(condStart)

        breakBlocks, continueBlocks = options.exitLoop()

        for block in breakBlocks:
            block.setNextBlock(end)

        for block in continueBlocks:
            block.setNextBlock(stepStart)

        return start, end

    def __str__(self):
        if self.start is None:
            raise TealCompileError("For expression must have a start", self)
        if self.cond is None:
            raise TealCompileError("For expression must have a condition", self)
        if self.step is None:
            raise TealCompileError("For expression must have a end", self)
        if self.doBlock is None:
            raise TealCompileError("For expression must have a doBlock", self)

        return "(For {} {} {} {})".format(
            self.start, self.cond, self.step, self.doBlock
        )

    def type_of(self):
        if self.doBlock is None:
            raise TealCompileError("For expression must have a doBlock", self)
        return TealType.none

    def has_return(self):
        return False

    def Do(self, doBlock: Expr):
        if self.doBlock is not None:
            raise TealCompileError("For expression already has a doBlock", self)
        require_type(doBlock.type_of(), TealType.none)
        self.doBlock = doBlock
        return self


For.__module__ = "pyteal"
