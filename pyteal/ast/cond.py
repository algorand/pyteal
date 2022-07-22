from typing import List, cast, TYPE_CHECKING
from pyteal.ast.seq import _use_seq_if_multiple

from pyteal.types import TealType, require_type
from pyteal.ir import TealOp, Op, TealSimpleBlock, TealConditionalBlock
from pyteal.errors import TealInputError
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


def _reformat_multi_argv(argv: tuple[list[Expr], ...]) -> list[list[Expr]]:
    """Reformat a list of lists of expressions with potentially multiple value expressions into a list of lists of expressions with only one value expression
        by using Seq blocks where appropriate.

    Example:
        [ [a, b, c], [d, e, f] ] -> [ [a, Seq(b, c)], [d, Seq(e, f)] ]
    """
    reformatted = []
    for arg in argv:
        # Note: this is not a valid Cond arg, but will be caught later in Cond.__init__()
        if len(arg) <= 1:
            reformatted.append(arg)
        else:
            reformatted.append([arg[0], _use_seq_if_multiple(arg[1:])])

    return reformatted


class Cond(Expr):
    """A chainable branching expression that supports an arbitrary number of conditions."""

    def __init__(self, *argv: List[Expr]):
        """Create a new Cond expression.

        At least one argument must be provided, and each argument must be a list with two or more elements.
        The first element is a condition which evalutes to uint64, and the remaining elements are the body
        of the condition, which will execute if that condition is true. The last elements of the condition bodies
        must have the same return type. During execution, each condition is tested in order, and the first
        condition to evaluate to a true value will cause its associated body to execute and become
        the value for this Cond expression. If no condition evalutes to a true value, the Cond
        expression produces an error and the TEAL program terminates.

        Example:
            .. code-block:: python

                Cond([Global.group_size() == Int(5), bid],
                    [Global.group_size() == Int(4), redeem, log],
                    [Global.group_size() == Int(1), wrapup])
        """
        super().__init__()

        if len(argv) < 1:
            raise TealInputError("Cond requires at least one [condition, value]")

        value_type = None
        sequenced_argv = _reformat_multi_argv(argv)

        for arg in sequenced_argv:
            msg = "Cond should be in the form of Cond([cond1, value1], [cond2, value2], ...), error in {}"
            if not isinstance(arg, list):
                raise TealInputError(msg.format(arg))
            if len(arg) != 2:
                raise TealInputError(msg.format(arg))

            require_type(arg[0], TealType.uint64)  # cond_n should be int

            if value_type is None:  # the types of all branches should be the same
                value_type = arg[1].type_of()
            else:
                require_type(arg[1], value_type)

        self.value_type = value_type
        self.args = sequenced_argv

    def __teal__(self, options: "CompileOptions"):
        start = None
        end = TealSimpleBlock([])
        prevBranch = None
        for i, (cond, pred) in enumerate(self.args):
            condStart, condEnd = cond.__teal__(options)
            predStart, predEnd = pred.__teal__(options)

            branchBlock = TealConditionalBlock([])
            branchBlock.setTrueBlock(predStart)

            condEnd.setNextBlock(branchBlock)
            predEnd.setNextBlock(end)
            if i == 0:
                start = condStart
            else:
                cast(TealConditionalBlock, prevBranch).setFalseBlock(condStart)
            prevBranch = branchBlock

        errBlock = TealSimpleBlock([TealOp(self, Op.err)])
        cast(TealConditionalBlock, prevBranch).setFalseBlock(errBlock)

        return start, end

    def __str__(self):
        ret_str = "(Cond"
        for a in self.args:
            ret_str += " [" + a[0].__str__() + ", " + a[1].__str__() + "]"
        ret_str += ")"
        return ret_str

    def type_of(self):
        return self.value_type

    def has_return(self):
        # this expression has a return op only if all possible conditions result in a return op
        return all(pred.has_return() for (_, pred) in self.args)


Cond.__module__ = "pyteal"
