from ..types import TealType, require_type, types_match
from ..ir import TealBlock
from ..util import new_label
from .expr import Expr

class If(Expr):
    """Simple two-way conditional expression."""

    def __init__(self, cond: Expr, thenBranch: Expr, elseBranch: Expr = None) -> None:
        """Create a new If expression.

        When this If expression is executed, the condition will be evaluated, and if it produces a
        true value, thenBranch will be executed and used as the return value for this expression.
        Otherwise, elseBranch will be executed and used as the return value, if it is provided.

        Args:
            cond: The condition to check. Must evaluate to uint64.
            thenBranch: Expression to evaluate if the condition is true.
            elseBranch (optional): Expression to evaluate if the condition is false. Must evaluate
                to the same type as thenBranch, if provided. Defaults to None.
        """
        require_type(cond.type_of(), TealType.uint64)

        if elseBranch is None:
            require_type(thenBranch.type_of(), TealType.none)
        else:
            require_type(thenBranch.type_of(), elseBranch.type_of())
        
        self.cond = cond
        self.thenBranch = thenBranch
        self.elseBranch = elseBranch

    def __teal__(self):
        condStart, condEnd = self.cond.__teal__()
        thenStart, thenEnd = self.thenBranch.__teal__()
        end = TealBlock([])

        condEnd.setTrueBlock(thenStart)
        thenEnd.setNextBlock(end)

        if self.elseBranch is None:
            condEnd.setFalseBlock(end)
        else:
            elseStart, elseEnd = self.elseBranch.__teal__()
            condEnd.setFalseBlock(elseStart)
            elseEnd.setNextBlock(end)

        return condStart, end

    def __str__(self):
        if self.elseBranch is None:
            return "(If {} {})".format(self.cond, self.thenBranch)
        return "(If {} {} {})".format(self.cond, self.thenBranch, self.elseBranch)

    def type_of(self):
        return self.thenBranch.type_of()

If.__module__ = "pyteal"
