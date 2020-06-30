from ..types import TealType, require_type, types_match
from ..ir import TealOp, Op, TealLabel
from ..util import new_label
from .expr import Expr

class If(Expr):
    """Simple two-way conditional expression."""

    def __init__(self, cond: Expr, thenBranch: Expr, elseBranch: Expr) -> None:
        """Create a new If expression.

        When this If expression is executed, the condition will be evaluated, and if it produces a
        true value, thenBranch will be executed and used as the return value for this expression.
        Otherwise, elseBranch will be executed and used as the return value.

        Args:
            cond: The condition to check. Must evaluate to uint64.
            thenBranch: Expression to evaluate if the condition is true.
            elseBranch: Expression to evaluate if the condition is false. Must evaluate to the same
            type as thenBranch.
        """
        require_type(cond.type_of(), TealType.uint64)
        require_type(thenBranch.type_of(), elseBranch.type_of())

        self.cond = cond
        self.thenBranch = thenBranch
        self.elseBranch = elseBranch

    def __teal__(self):
        cond = self.cond.__teal__()
        l1 = new_label()
        t_branch = self.thenBranch.__teal__()
        e_branch = self.elseBranch.__teal__()
        l2 = new_label()

        teal = cond
        teal.append(TealOp(Op.bnz, l1))
        teal += e_branch
        teal.append(TealOp(Op.b, l2))
        teal.append(TealLabel(l1))
        teal += t_branch
        teal.append(TealLabel(l2))

        return teal

    def __str__(self):
        return "(If {} {} {})".format(self.cond, self.thenBranch, self.elseBranch)

    def type_of(self):
        return self.thenBranch.type_of()
