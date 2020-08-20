from typing import List

from ..types import TealType, require_type
from ..errors import TealInputError
from .expr import Expr

class Seq(Expr):
    """A control flow expression to represent a sequence of expressions."""
    
    def __init__(self, exprs: List[Expr]):
        """Create a new Seq expression.

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
        if len(exprs) == 0:
            raise TealInputError("Seq requires children.")
        for i, expr in enumerate(exprs):
            if not isinstance(expr, Expr):
                raise TealInputError("{} is not a pyteal expression.".format(expr))
            if i + 1 < len(exprs):
                require_type(expr.type_of(), TealType.none)
        
        self.args = exprs
        
    def __teal__(self):
        code = []
        for a in self.args:
            code += a.__teal__()
        return code

    def __str__(self):
        ret_str = "(Seq"
        for a in self.args:
            ret_str += " " + a.__str__()
        ret_str += ")"
        return ret_str
        
    def type_of(self):
        return self.args[-1].type_of()

Seq.__module__ = "pyteal"
