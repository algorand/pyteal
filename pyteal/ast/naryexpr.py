from typing import Sequence

from ..types import TealType, require_type
from ..errors import TealInputError
from .expr import Expr

class NaryExpr(Expr):
    """N-ary expression base class.
    
    This type of expression takes an arbitrary number of arguments.
    """
    
    def __init__(self, op: str, inputType: TealType, outputType: TealType, args: Sequence[Expr]):
        if len(args) < 2:
            raise TealInputError("NaryExpr requires at least two children.")
        for arg in args:
            if not isinstance(arg, Expr):
                raise TealInputError("Argument is not a pyteal expression: {}".format(arg))
            require_type(arg.type_of(), inputType)

        self.op = op
        self.outputType = outputType
        self.args = args
    
    def __teal__(self):
        code = []
        for i, a in enumerate(self.args):
            code += a.__teal__()
            if i != 0:
                code.append([self.op])
        return code

    def __str__(self):
        ret_str = "(" + self.op,
        for a in self.args:
            ret_str += " " + a.__str__()
        ret_str += ")"
        return ret_str

    def type_of(self):
        return self.outputType

def And(*args: Expr):
    """Logical and expression.

    Produces 1 if all arguments are nonzero. Otherwise produces 0.
    
    All arguments must be PyTeal expressions that evaluate to uint64, and there must be at least two
    arguments.
    """
    return NaryExpr("&&", TealType.uint64, TealType.uint64, args)

def Or(*args: Expr):
    """Logical or expression.
    
    Produces 1 if any argument is nonzero. Otherwise produces 0.
    
    All arguments must be PyTeal expressions that evaluate to uint64, and there must be at least two
    arguments.
    """
    return NaryExpr("||", TealType.uint64, TealType.uint64, args)
