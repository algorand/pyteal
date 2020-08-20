from ..types import TealType, require_type
from ..ir import TealOp, Op
from .expr import Expr

class BinaryExpr(Expr):
    """An expression with two arguments."""

    def __init__(self, op: Op, inputType: TealType, outputType: TealType, argLeft: Expr, argRight: Expr) -> None:
        require_type(argLeft.type_of(), inputType)
        require_type(argRight.type_of(), inputType)
        self.op = op
        self.outputType = outputType
        self.argLeft = argLeft
        self.argRight = argRight

    def __teal__(self):
        teal = self.argLeft.__teal__() + self.argRight.__teal__()
        teal.append(TealOp(self.op))
        return teal
    
    def __str__(self):
        return "({} {} {})".format(self.op.value, self.argLeft, self.argRight)
    
    def type_of(self):
        return self.outputType

BinaryExpr.__module__ = "pyteal"

def Add(left: Expr, right: Expr) -> BinaryExpr:
    """Add two numbers.
    
    Produces left + right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.add, TealType.uint64, TealType.uint64, left, right)

def Minus(left: Expr, right: Expr) -> BinaryExpr:
    """Subtract two numbers.
    
    Produces left - right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.minus, TealType.uint64, TealType.uint64, left, right)

def Mul(left: Expr, right: Expr) -> BinaryExpr:
    """Multiply two numbers.
    
    Produces left * right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.mul, TealType.uint64, TealType.uint64, left, right)

def Div(left: Expr, right: Expr) -> BinaryExpr:
    """Divide two numbers.
    
    Produces left / right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.div, TealType.uint64, TealType.uint64, left, right)

def Mod(left: Expr, right: Expr) -> BinaryExpr:
    """Modulo expression.
    
    Produces left % right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.mod, TealType.uint64, TealType.uint64, left, right)

def BitwiseAnd(left: Expr, right: Expr) -> BinaryExpr:
    """Bitwise and expression.

    Produces left & right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.bitwise_and, TealType.uint64, TealType.uint64, left, right)

def BitwiseOr(left: Expr, right: Expr) -> BinaryExpr:
    """Bitwise or expression.

    Produces left | right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.bitwise_or, TealType.uint64, TealType.uint64, left, right)

def BitwiseXor(left: Expr, right: Expr) -> BinaryExpr:
    """Bitwise xor expression.

    Produces left ^ right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.bitwise_xor, TealType.uint64, TealType.uint64, left, right)

def Eq(left: Expr, right: Expr) -> BinaryExpr:
    """Equality expression.
    
    Checks if left == right.

    Args:
        left: A value to check.
        right: The other value to check. Must evaluate to the same type as left.
    """
    return BinaryExpr(Op.eq, right.type_of(), TealType.uint64, left, right)

def Neq(left: Expr, right: Expr) -> BinaryExpr:
    """Difference expression.
    
    Checks if left != right.

    Args:
        left: A value to check.
        right: The other value to check. Must evaluate to the same type as left.
    """
    return BinaryExpr(Op.neq, right.type_of(), TealType.uint64, left, right)

def Lt(left: Expr, right: Expr) -> BinaryExpr:
    """Less than expression.
    
    Checks if left < right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.lt, TealType.uint64, TealType.uint64, left, right)

def Le(left: Expr, right: Expr) -> BinaryExpr:
    """Less than or equal to expression.
    
    Checks if left <= right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.le, TealType.uint64, TealType.uint64, left, right)

def Gt(left: Expr, right: Expr) -> BinaryExpr:
    """Greater than expression.
    
    Checks if left > right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.gt, TealType.uint64, TealType.uint64, left, right)

def Ge(left: Expr, right: Expr) -> BinaryExpr:
    """Greater than or equal to expression.
    
    Checks if left >= right.
    
    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.ge, TealType.uint64, TealType.uint64, left, right)
