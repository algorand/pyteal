from typing import TYPE_CHECKING, cast

from ..errors import TealCompileError, TealInputError
from ..types import TealType, require_type, types_match
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
        self.doBlock = None
        self.step = None

    def __teal__(self, options: 'CompileOptions'):
        if self.doBlock is None:
            raise TealCompileError("While expression must have a doBlock", self)

        condStart, condEnd = self.cond.__teal__(options)
        doStart, doEnd = self.doBlock.__teal__(options)

        end = TealSimpleBlock([])

        if self.step:
            stepStart, stepEnd = self.step.__teal__(options)
            stepEnd.setNextBlock(condStart)
            doEnd.setNextBlock(stepStart)
        else:
            doEnd.setNextBlock(condStart)


        branchBlock = TealConditionalBlock([])
        branchBlock.setTrueBlock(doStart)
        branchBlock.setFalseBlock(end)

        condEnd.setNextBlock(branchBlock)
        condStart.addIncoming(doEnd)



        return condStart, end

    def __str__(self):
        if self.doBlock is None:
            raise TealCompileError("While expression must have a doBlock", self)
        
        return "(While {} {})".format(self.cond, self.doBlock)

    def type_of(self):
        if self.doBlock is None:
            raise TealCompileError("While expression must have a doBlock", self) 
        return self.doBlock.type_of()

    def Do(self, doBlock: Seq):
        self.doBlock=doBlock
        return self

While.__module__ = "pyteal"