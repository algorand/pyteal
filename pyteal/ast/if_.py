from ..types import TealType, require_type, types_match
from ..ir import TealOp, Op, TealLabel
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
        teal = self.cond.__teal__()
        end = new_label()
        tealThen = self.thenBranch.__teal__()
        tealElse = [] if self.elseBranch is None else self.elseBranch.__teal__()

        if self.elseBranch is None:
            teal.append(TealOp(Op.bz, end))
            teal += tealThen
        else:
            # doing this swap so that labels remain consistent with previous If implementation.
            then = end
            end = new_label()

            teal.append(TealOp(Op.bnz, then))
            teal += tealElse
            teal.append(TealOp(Op.b, end))
            teal.append(TealLabel(then))
            teal += tealThen
        
        teal.append(TealLabel(end))

        return teal

    def __str__(self):
        if self.elseBranch is None:
            return "(If {} {})".format(self.cond, self.thenBranch)
        return "(If {} {} {})".format(self.cond, self.thenBranch, self.elseBranch)

    def type_of(self):
        return self.thenBranch.type_of()

If.__module__ = "pyteal"
