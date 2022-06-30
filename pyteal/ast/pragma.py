from typing import TYPE_CHECKING, Any

from pyteal.ast.expr import Expr
from pyteal.ast.leafexpr import LeafExpr
from pyteal.pragma import is_valid_compiler_version, pragma

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Pragma(LeafExpr):
    """A meta expression which defines a pragma for a specific subsection of PyTeal code.

    This expression does not affect the underlying compiled TEAL code in any way."""

    def __init__(self, child: Expr, *, compiler_version: str, **kwargs: Any) -> None:
        super().__init__()

        self.child = child

        if not is_valid_compiler_version(compiler_version):
            raise ValueError("Invalid compiler version: {}".format(compiler_version))
        self.compiler_version = compiler_version

    def __teal__(self, options: "CompileOptions"):
        pragma(compiler_version=self.compiler_version)

        return self.child.__teal__(options)

    def __str__(self):
        return "(pragma {})".format(self.child)

    def type_of(self):
        return self.child.type_of()

    def has_return(self):
        return self.child.has_return()


Pragma.__module__ = "pyteal"
