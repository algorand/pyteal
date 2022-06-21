from typing import TYPE_CHECKING, Tuple

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

        # TODO: make sure this doesnt cause issues
        if len(tsb.ops) > 0:
            tsb.ops[-1].args.append(f"// {self.comment}")
        else:
            tb.ops[-1].args.append(f"// {self.comment}")

        return tb, tsb

    def __str__(self):
        return f"(Comment {self.comment} ({self.expr}))"

    def type_of(self):
        return self.expr.type_of()

    def has_return(self):
        return self.expr.has_return()


Comment.__module__ = "pyteal"
