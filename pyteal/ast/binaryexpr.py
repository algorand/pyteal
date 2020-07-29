from ..types import TealType, require_type, types_match
from ..errors import TealTypeMismatchError
from .expr import Expr

class BinaryExpr(Expr):
    """An expression with two arguments."""

    def __init__(self, op: str, inputType: TealType, outputType: TealType, argLeft: Expr, argRight: Expr) -> None:
        require_type(argLeft.type_of(), inputType)
        require_type(argRight.type_of(), inputType)
        self.op = op
        self.outputType = outputType
        self.argLeft = argLeft
        self.argRight = argRight
    
    def __teal__(self):
        teal = self.argLeft.__teal__() + self.argRight.__teal__()
        teal.append([self.op])
        return teal

    def __str__(self):
        return "({} {} {})".format(self.op, self.argLeft, self.argRight)

    def type_of(self):
        return self.outputType

def Add(left: Expr, right: Expr):
    """Add two numbers.
    
    Produces left + right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr("+", TealType.uint64, TealType.uint64, left, right)

def Minus(left: Expr, right: Expr):
    """Subtract two numbers.
    
    Produces left - right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr("-", TealType.uint64, TealType.uint64, left, right)

def Mul(left: Expr, right: Expr):
    """Multiply two numbers.
    
    Produces left * right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr("*", TealType.uint64, TealType.uint64, left, right)

def Div(left: Expr, right: Expr):
    """Divide two numbers.
    
    Produces left / right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr("/", TealType.uint64, TealType.uint64, left, right)

def Mod(left: Expr, right: Expr):
    """Modulo expression.
    
    Produces left % right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr("%", TealType.uint64, TealType.uint64, left, right)

def Eq(left: Expr, right: Expr):
    """Equality expression.
    
    Checks if left == right.

    Args:
        left: A value to check.
        right: The other value to check. Must evaluate to the same type as left.
    """
    # a hack to make this op emit TealTypeMismatchError instead of TealTypeError
    t1 = left.type_of()
    t2 = right.type_of()
    if not types_match(t1, t2):
        raise TealTypeMismatchError(t1, t2)
    return BinaryExpr("==", TealType.anytype, TealType.uint64, left, right)

def Lt(left: Expr, right: Expr):
    """Less than expression.
    
    Checks if left < right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr("<", TealType.uint64, TealType.uint64, left, right)

def Le(left: Expr, right: Expr):
    """Less than or equal to expression.
    
    Checks if left <= right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr("<=", TealType.uint64, TealType.uint64, left, right)

def Gt(left: Expr, right: Expr):
    """Greater than expression.
    
    Checks if left > right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(">", TealType.uint64, TealType.uint64, left, right)

def Ge(left: Expr, right: Expr):
    """Greater than or equal to expression.
    
    Checks if left >= right.
    
    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(">=", TealType.uint64, TealType.uint64, left, right)
