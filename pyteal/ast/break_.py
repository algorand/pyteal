from typing import TYPE_CHECKING

from ..types import TealType
from ..errors import TealCompileError
from .expr import Expr
from ..ir import TealSimpleBlock


if TYPE_CHECKING:
    from ..compiler import CompileOptions


class Break(Expr):
    """A break expression"""

    def __init__(self) -> None:
        """Create a new break expression.

        This operation is only permitted in a loop.

        """
        super().__init__()

    def __str__(self) -> str:
        return "break"

    def __teal__(self, options: "CompileOptions"):
        if not options.isInLoop():
            raise TealCompileError("break is only allowed in a loop", self)

        start = TealSimpleBlock([])
        options.addLoopBreakBlock(start)

        return start, start

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


Break.__module__ = "pyteal"
