from typing import Union, TYPE_CHECKING

from ..types import TealType
from ..ir import TealOp, Op, TealBlock
from ..errors import TealInputError
from .leafexpr import LeafExpr
from .expr import Expr
from .seq import Seq
from .while_ import While

if TYPE_CHECKING:
    from ..compiler import CompileOptions

class For(Expr):
    """For expression."""

    def __init__(self, cond: Expr, thenBranch: Expr) -> None:
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

        self.cond = cond
        self.thenBranch = thenBranch

    def __teal__(self, options: 'CompileOptions'):
        if self.thenBranch is None:
            raise TealCompileError("For expression must have a thenBranch", self)

        return While.__teal__(self)

    def __str__(self):
        if self.thenBranch is None:
            raise TealCompileError("For expression must have a thenBranch", self)
        
        return "(For {} {})".format(self.cond, self.thenBranch)

    def type_of(self):
        if self.thenBranch is None:
            raise TealCompileError("For expression must have a thenBranch", self) 
        return self.thenBranch.type_of()

    def Do(self, thenBranch: Seq):
        return While.Do(self)

While.__module__ = "pyteal"