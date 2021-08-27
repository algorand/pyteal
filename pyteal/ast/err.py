from typing import TYPE_CHECKING

from ..types import TealType
from ..ir import TealOp, Op, TealBlock
from .expr import Expr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class Err(Expr):
    """Expression that causes the program to immediately fail when executed."""

    def __teal__(self, options: "CompileOptions"):
        op = TealOp(self, Op.err)
        return TealBlock.FromOp(options, op)

    def __str__(self):
        return "(err)"

    def type_of(self):
        return TealType.none

    def has_return(self):
        return True


Err.__module__ = "pyteal"
