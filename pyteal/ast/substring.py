from typing import TYPE_CHECKING

from ..types import TealType, require_type
from ..ir import TealOp, Op, TealBlock
from .expr import Expr

if TYPE_CHECKING:
    from ..compiler import CompileOptions

class Substring(Expr):
    """Take a substring of a byte string."""

    def __init__(self, string: Expr, start: Expr, end: Expr) -> None:
        """Create a new Substring expression.

        Produces a new byte string consisting of the bytes starting at start up to but not including
        end.

        Args:
            string: The byte string.
            start: The starting index for the substring.
            end: The ending index for the substring.
        """
        super().__init__()
        
        require_type(string.type_of(), TealType.bytes)
        require_type(start.type_of(), TealType.uint64)
        require_type(end.type_of(), TealType.uint64)
        
        self.string = string
        self.start = start
        self.end = end

    def __teal__(self, options: 'CompileOptions'):
        return TealBlock.FromOp(options, TealOp(self, Op.substring3), self.string, self.start, self.end)

    def __str__(self):
        return "(substring {} {} {})".format(self.string, self.start, self.end)
    
    def type_of(self):
        return TealType.bytes

Substring.__module__ = "pyteal"
