from typing import TYPE_CHECKING, Tuple

from pyteal.errors import TealInputError
from pyteal.types import TealType
from pyteal.ir import TealBlock, TealSimpleBlock, TealOp, Op
from pyteal.ast.expr import Expr
from pyteal.ast.seq import Seq

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class CommentExpr(Expr):
    """Represents a single line comment in TEAL source code.

    This class is intentionally hidden because it's too basic to directly expose. Anything exposed
    to users should be able to handle multi-line comments by breaking them apart and using this
    class.
    """

    def __init__(self, single_line_comment: str) -> None:
        super().__init__()
        if "\n" in single_line_comment or "\r" in single_line_comment:
            raise TealInputError(
                "Newlines should not be present in the CommentExpr constructor"
            )
        self.comment = single_line_comment

    def __teal__(self, options: "CompileOptions") -> Tuple[TealBlock, TealSimpleBlock]:
        op = TealOp(self, Op.comment, self.comment)
        return TealBlock.FromOp(options, op)

    def __str__(self):
        return f'(Comment "{self.comment}")'

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


CommentExpr.__module__ = "pyteal"


def Comment(expr: Expr, comment: str) -> Expr:
    """Wrap an existing expression with a comment.

    This comment will be present in the compiled TEAL source immediately before the first op of the
    expression.

    Note that when TEAL source is assembled into bytes, all comments are omitted.

    Args:
        expr: The expression to be commented.
        comment: The comment that will be associated with the expression.

    Returns:
        A new expression which is functionally equivalent to the input expression, but which will
        compile with the given comment string.
    """
    lines = comment.splitlines()
    if type(expr) is Seq and len(expr.args) == 0:
        return Seq()
    return Seq(*[CommentExpr(line) for line in lines], expr)
