from typing import List, TYPE_CHECKING, overload

from pyteal.types import TealType, require_type
from pyteal.errors import TealInputError
from pyteal.ir import TealSimpleBlock
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Seq(Expr):
    """A control flow expression to represent a sequence of expressions."""

    @overload
    def __init__(self, *exprs: Expr) -> None:
        pass

    @overload
    def __init__(self, exprs: List[Expr]) -> None:
        pass

    def __init__(self, *exprs):
        """
        __init__(*exprs: Expr) -> None
        __init__(exprs: List[Expr]) -> None

        Create a new Seq expression.

        The new Seq expression will take on the return value of the final expression in the sequence.

        Args:
            exprs: The expressions to include in this sequence. All expressions that are not the
                final one in this list must not return any values.

        Example:
            .. code-block:: python

                Seq([
                    App.localPut(Bytes("key"), Bytes("value")),
                    Int(1)
                ])
        """
        super().__init__()

        # Handle case where a list of expressions is provided
        if len(exprs) == 1 and isinstance(exprs[0], list):
            exprs = exprs[0]

        for i, expr in enumerate(exprs):
            if not isinstance(expr, Expr):
                raise TealInputError("{} is not a pyteal expression.".format(expr))
            if i + 1 < len(exprs):
                require_type(expr, TealType.none)

        self.args = exprs

    def __teal__(self, options: "CompileOptions"):
        start = TealSimpleBlock([])
        end = start
        for arg in self.args:
            argStart, argEnd = arg.__teal__(options)
            end.setNextBlock(argStart)
            end = argEnd
        return start, end

    def __str__(self):
        ret_str = "(Seq"
        for a in self.args:
            ret_str += " " + a.__str__()
        ret_str += ")"
        return ret_str

    def type_of(self):
        if len(self.args) == 0:
            return TealType.none
        return self.args[-1].type_of()

    def has_return(self):
        # this expression declares it has a return op only if its final expression has a return op
        # TODO: technically if ANY expression, not just the final one, returns true for has_return,
        # this could return true as well. But in that case all expressions after the one that
        # returns true for has_return is dead code, so it could be optimized away
        if len(self.args) == 0:
            return False
        return self.args[-1].has_return()


Seq.__module__ = "pyteal"


@overload
def _use_seq_if_multiple(exprs: list[Expr]) -> Expr:
    ...


@overload
def _use_seq_if_multiple(*exprs: Expr) -> Expr:
    ...


def _use_seq_if_multiple(*exprs):
    """If multiple expressions are provided, wrap them in a Seq expression."""

    # Guard against no expressions
    if len(exprs) == 0:
        raise TealInputError("Expressions cannot be empty.")

    # Handle case where a list of expressions is provided
    if len(exprs) == 1 and isinstance(exprs[0], list):
        exprs = exprs[0]

    if len(exprs) > 1:
        return Seq(*exprs)
    return exprs[0]
