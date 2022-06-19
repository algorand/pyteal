from typing import TYPE_CHECKING, Tuple

from pyteal.types import TealType
from pyteal.ir import TealBlock, TealSimpleBlock
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Comment(Expr):
    def __init__(self, expr: Expr, comment: str):
        self.expr = expr
        self.comment = comment

    def __teal__(self, options: "CompileOptions") -> Tuple[TealBlock, TealSimpleBlock]:
        tb, tsb = self.expr.__teal__(options)
        # tb.ops[-1].args.append("// "+self.comment)
        tsb.ops[-1].args.append("// " + self.comment)
        return tb, tsb

    def __str__(self):
        return "(Comment {} ({}))".format(self.comment, str(self.expr))

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


Comment.__module__ = "pyteal"
