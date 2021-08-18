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

    def __init__(self, start: Expr, cond: Expr, end:Expr) -> None:
        """Create a new For expression.

        When this For expression is executed, the condition will be evaluated, and if it produces a
        true value, doBlock will be executed and return to the start of the expression execution.
        Otherwise, no branch will be executed. 

        Args:
            start: Expression setting the variable's initial value
            cond: The condition to check. Must evaluate to uint64.
            end: Expression to update the variable's value.
        """
        super().__init__()
        require_type(cond.type_of(), TealType.uint64)

        self.start = start
        self.cond = cond
        self.step = end
        self.doBlock: Optional[Seq] = None

    def __teal__(self, options: 'CompileOptions'):
        if self.doBlock is None:
            raise TealCompileError("While expression must have a doBlock", self)

        breakBlocks = options.breakBlocks
        continueBlocks = options.continueBlocks
        prevLoop = options.currentLoop

        options.breakBlocks = []
        options.continueBlocks = []
        options.currentLoop = self

        end = TealSimpleBlock([])
        start, startEnd = self.start.__teal__(options)
        condStart, condEnd = self.cond.__teal__(options)
        doStart, doEnd = self.doBlock.__teal__(options)



        stepStart, stepEnd = self.step.__teal__(options)
        stepEnd.setNextBlock(condStart)
        doEnd.setNextBlock(stepStart)

        for block in options.breakBlocks:
            block.setNextBlock(end)

        for block in options.continueBlocks:
            block.setNextBlock(stepStart)
            doEnd.setNextBlock(block)

        options.breakBlocks = breakBlocks
        options.continueBlocks = continueBlocks
        options.currentLoop = prevLoop

        branchBlock = TealConditionalBlock([])
        branchBlock.setTrueBlock(doStart)
        branchBlock.setFalseBlock(end)

        condEnd.setNextBlock(branchBlock)
        condStart.addIncoming(doStart)

        startEnd.nextBlock = condStart

        return start, end

    def __str__(self):
        if self.start is None:
            raise TealCompileError("For expression must have a start", self)
        if self.cond is None:
            raise TealCompileError("For expression must have a condition", self)
        if self.step is None:
            raise TealCompileError("For expression must have a end", self)
        if self.doBlock is None:
            raise TealCompileError("For expression must have a thenBranch", self)
        
        return "(For {} {} {} {})".format(self.start, self.cond, self.step, self.doBlock)

    def type_of(self):
        if str(self.doBlock) == str(Seq([Int(0)])):
            raise TealCompileError("For expression must have a thenBranch", self) 
        return self.doBlock.type_of()

    def Do(self, doBlock: Seq):
        self.doBlock = doBlock
        return self

While.__module__ = "pyteal"