from typing import Union, TYPE_CHECKING

from ..types import TealType, require_type
from ..ir import TealOp, Op, TealBlock
from ..errors import TealCompileError
from .leafexpr import LeafExpr
from .expr import Expr
from .seq import Seq
from .while_ import While

if TYPE_CHECKING:
    from ..compiler import CompileOptions

class For(Expr):
    """For expression."""

    def __init__(self, start: Expr, cond: Expr, end:Expr) -> None:
        """Create a new For expression.

        When this For expression is executed, the condition will be evaluated, and if it produces a
        true value, thenBranch will be executed and return to the start of the expression execution.
        Otherwise, no branch will be executed. 

        Args:
            cond: The condition to check. Must evaluate to uint64.
            thenBranch: Expression to evaluate if the condition is true.
        """
        super().__init__()
        require_type(cond.type_of(), TealType.uint64)

        self.start = start
        self.cond = cond
        self.step = end
        self.doBlock = None

    def __teal__(self, options: 'CompileOptions'):
        if self.doBlock is None:
            raise TealCompileError("For expression must have a thenBranch", self)

        start, end = self.start.__teal__(options)

        bodyStart, _= While.__teal__(self,self.cond)

        end.nextBlock = bodyStart

        return start,end

    def __str__(self):
        if self.start is None:
            raise TealCompileError("For expression must have a start", self)
        if self.cond is None:
            raise TealCompileError("For expression must have a condition", self)
        if self.end is None:
            raise TealCompileError("For expression must have a end", self)
        if self.doBlock is None:
            raise TealCompileError("For expression must have a thenBranch", self)
        
        return "(For {} {} {} {})".format(self.start, self.cond, self.end, self.doBlock)

    def type_of(self):
        if self.doBlock is None:
            raise TealCompileError("For expression must have a thenBranch", self) 
        return self.doBlock.type_of()

    def Do(self, doBlock: Seq):
        self.doBlock = doBlock
        return self

While.__module__ = "pyteal"