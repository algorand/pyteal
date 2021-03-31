from typing import Union, Tuple, cast, TYPE_CHECKING

from ..types import TealType, require_type
from ..ir import TealOp, Op, TealBlock
from .expr import Expr

if TYPE_CHECKING:
    from ..compiler import CompileOptions

class BinaryExpr(Expr):
    """An expression with two arguments."""

    def __init__(self, op: Op, inputType: Union[TealType, Tuple[TealType, TealType]], outputType: TealType, argLeft: Expr, argRight: Expr) -> None:
        super().__init__()
        leftType, rightType = cast(Tuple[TealType, TealType], inputType) if type(inputType) == tuple else (inputType, inputType)
        require_type(argLeft.type_of(), leftType)
        require_type(argRight.type_of(), rightType)

        self.op = op
        self.outputType = outputType
        self.argLeft = argLeft
        self.argRight = argRight

    def __teal__(self, options: 'CompileOptions'):
        return TealBlock.FromOp(options, TealOp(self, self.op), self.argLeft, self.argRight)
    
    def __str__(self):
        return "({} {} {})".format(self.op, self.argLeft, self.argRight)
    
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

def GetBit(value: Expr, index: Expr) -> BinaryExpr:
    """Get the bit value of an expression at a specific index.

    The meaning of index differs if value is an integer or a byte string.

    * For integers, bit indexing begins with low-order bits. For example, :code:`GetBit(Int(16), Int(4))`
      yields 1. Any other valid index would yield a bit value of 0. Any integer less than 64 is a
      valid index.
    
    * For byte strings, bit indexing begins at the first byte. For example, :code:`GetBit(Bytes("base16", "0xf0"), Int(0))`
      yields 1. Any index less than 4 would yield 1, and any valid index 4 or greater would yield 0.
      Any integer less than 8*Len(value) is a valid index.

    Requires TEAL version 3 or higher.

    Args:
        value: The value containing bits. Can evaluate to any type.
        index: The index of the bit to extract. Must evaluate to uint64.
    """
    return BinaryExpr(Op.getbit, (TealType.anytype, TealType.uint64), TealType.uint64, value, index)

def GetByte(value: Expr, index: Expr) -> BinaryExpr:
    """Extract a single byte as an integer from a byte string.

    Similar to GetBit, indexing begins at the first byte. For example, :code:`GetByte(Bytes("base16", "0xff0000"), Int(0))`
    yields 255. Any other valid index would yield 0.

    Requires TEAL version 3 or higher.

    Args:
        value: The value containing the bytes. Must evaluate to bytes.
        index: The index of the byte to extract. Must evaluate to an integer less than Len(value).
    """
    return BinaryExpr(Op.getbyte, (TealType.bytes, TealType.uint64), TealType.uint64, value, index)
