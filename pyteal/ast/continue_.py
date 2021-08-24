from typing import TYPE_CHECKING

from ..types import TealType
from ..errors import TealCompileError
from .expr import Expr
from ..ir import TealSimpleBlock


if TYPE_CHECKING:
    from ..compiler import CompileOptions


class Continue(Expr):
    """A continue expression"""

    def __init__(self) -> None:
        """Create a new continue expression.

        This operation is only permitted in a loop.

        """
        super().__init__()

    def __str__(self) -> str:
        return "continue"

    def __teal__(self, options: "CompileOptions"):
        if not options.isInLoop():
            raise TealCompileError("continue is only allowed in a loop", self)

        start = TealSimpleBlock([])
        options.addLoopContinueBlock(start)

        return start, start

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


Continue.__module__ = "pyteal"
