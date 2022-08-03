from typing import Union, Tuple, cast, TYPE_CHECKING

from pyteal.types import TealType, require_type
from pyteal.errors import verifyProgramVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class BinaryExpr(Expr):
    """An expression with two arguments."""

    def __init__(
        self,
        op: Op,
        inputType: Union[TealType, Tuple[TealType, TealType]],
        outputType: TealType,
        argLeft: Expr,
        argRight: Expr,
    ) -> None:
        super().__init__()
        if type(inputType) is tuple:
            leftType, rightType = inputType
        else:
            leftType = cast(TealType, inputType)
            rightType = leftType
        require_type(argLeft, leftType)
        require_type(argRight, rightType)

        self.op = op
        self.outputType = outputType
        self.argLeft = argLeft
        self.argRight = argRight

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            self.op.min_version,
            options.version,
            "Program version too low to use op {}".format(self.op),
        )

        return TealBlock.FromOp(
            options, TealOp(self, self.op), self.argLeft, self.argRight
        )

    def __str__(self):
        return "({} {} {})".format(
            str(self.op).title().replace("_", ""), self.argLeft, self.argRight
        )

    def type_of(self):
        return self.outputType

    def has_return(self):
        return False


BinaryExpr.__module__ = "pyteal"


def Minus(left: Expr, right: Expr) -> Expr:
    """Subtract two numbers.

    Produces left - right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.minus, TealType.uint64, TealType.uint64, left, right)


def Div(left: Expr, right: Expr) -> Expr:
    """Divide two numbers.

    Produces left / right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.div, TealType.uint64, TealType.uint64, left, right)


def Mod(left: Expr, right: Expr) -> Expr:
    """Modulo expression.

    Produces left % right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.mod, TealType.uint64, TealType.uint64, left, right)


def Exp(a: Expr, b: Expr) -> Expr:
    """Exponential expression.

    Produces a ** b.

    Requires program version 4 or higher.

    Args:
        a: Must evaluate to uint64.
        b: Must evaluate to uint64.
    """
    return BinaryExpr(Op.exp, TealType.uint64, TealType.uint64, a, b)


def BitwiseAnd(left: Expr, right: Expr) -> Expr:
    """Bitwise and expression.

    Produces left & right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.bitwise_and, TealType.uint64, TealType.uint64, left, right)


def BitwiseOr(left: Expr, right: Expr) -> Expr:
    """Bitwise or expression.

    Produces left | right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.bitwise_or, TealType.uint64, TealType.uint64, left, right)


def BitwiseXor(left: Expr, right: Expr) -> Expr:
    """Bitwise xor expression.

    Produces left ^ right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.bitwise_xor, TealType.uint64, TealType.uint64, left, right)


def ShiftLeft(a: Expr, b: Expr) -> Expr:
    """Bitwise left shift expression.

    Produces a << b. This is equivalent to a times 2^b, modulo 2^64.

    Requires program version 4 or higher.

    Args:
        a: Must evaluate to uint64.
        b: Must evaluate to uint64.
    """
    return BinaryExpr(Op.shl, TealType.uint64, TealType.uint64, a, b)


def ShiftRight(a: Expr, b: Expr) -> Expr:
    """Bitwise right shift expression.

    Produces a >> b. This is equivalent to a divided by 2^b.

    Requires program version 4 or higher.

    Args:
        a: Must evaluate to uint64.
        b: Must evaluate to uint64.
    """
    return BinaryExpr(Op.shr, TealType.uint64, TealType.uint64, a, b)


def Eq(left: Expr, right: Expr) -> Expr:
    """Equality expression.

    Checks if left == right.

    Args:
        left: A value to check.
        right: The other value to check. Must evaluate to the same type as left.
    """
    return BinaryExpr(Op.eq, right.type_of(), TealType.uint64, left, right)


def Neq(left: Expr, right: Expr) -> Expr:
    """Difference expression.

    Checks if left != right.

    Args:
        left: A value to check.
        right: The other value to check. Must evaluate to the same type as left.
    """
    return BinaryExpr(Op.neq, right.type_of(), TealType.uint64, left, right)


def Lt(left: Expr, right: Expr) -> Expr:
    """Less than expression.

    Checks if left < right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.lt, TealType.uint64, TealType.uint64, left, right)


def Le(left: Expr, right: Expr) -> Expr:
    """Less than or equal to expression.

    Checks if left <= right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.le, TealType.uint64, TealType.uint64, left, right)


def Gt(left: Expr, right: Expr) -> Expr:
    """Greater than expression.

    Checks if left > right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.gt, TealType.uint64, TealType.uint64, left, right)


def Ge(left: Expr, right: Expr) -> Expr:
    """Greater than or equal to expression.

    Checks if left >= right.

    Args:
        left: Must evaluate to uint64.
        right: Must evaluate to uint64.
    """
    return BinaryExpr(Op.ge, TealType.uint64, TealType.uint64, left, right)


def GetBit(value: Expr, index: Expr) -> Expr:
    """Get the bit value of an expression at a specific index.

    The meaning of index differs if value is an integer or a byte string.

    * For integers, bit indexing begins with low-order bits. For example, :code:`GetBit(Int(16), Int(4))`
      yields 1. Any other valid index would yield a bit value of 0. Any integer less than 64 is a
      valid index.

    * For byte strings, bit indexing begins at the first byte. For example, :code:`GetBit(Bytes("base16", "0xf0"), Int(0))`
      yields 1. Any index less than 4 would yield 1, and any valid index 4 or greater would yield 0.
      Any integer less than 8*Len(value) is a valid index.

    Requires program version 3 or higher.

    Args:
        value: The value containing bits. Can evaluate to any type.
        index: The index of the bit to extract. Must evaluate to uint64.
    """
    return BinaryExpr(
        Op.getbit, (TealType.anytype, TealType.uint64), TealType.uint64, value, index
    )


def GetByte(value: Expr, index: Expr) -> Expr:
    """Extract a single byte as an integer from a byte string.

    Similar to GetBit, indexing begins at the first byte. For example, :code:`GetByte(Bytes("base16", "0xff0000"), Int(0))`
    yields 255. Any other valid index would yield 0.

    Requires program version 3 or higher.

    Args:
        value: The value containing the bytes. Must evaluate to bytes.
        index: The index of the byte to extract. Must evaluate to an integer less than Len(value).
    """
    return BinaryExpr(
        Op.getbyte, (TealType.bytes, TealType.uint64), TealType.uint64, value, index
    )


def BytesAdd(left: Expr, right: Expr) -> Expr:
    """Add two numbers as bytes.

    Produces left + right, where left and right are interpreted as big-endian unsigned integers.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_add, TealType.bytes, TealType.bytes, left, right)


def BytesMinus(left: Expr, right: Expr) -> Expr:
    """Subtract two numbers as bytes.

    Produces left - right, where left and right are interpreted as big-endian unsigned integers.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_minus, TealType.bytes, TealType.bytes, left, right)


def BytesDiv(left: Expr, right: Expr) -> Expr:
    """Divide two numbers as bytes.

    Produces left / right, where left and right are interpreted as big-endian unsigned integers.
    Arguments must not exceed 64 bytes.

    Panics if right is 0.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_div, TealType.bytes, TealType.bytes, left, right)


def BytesMul(left: Expr, right: Expr) -> Expr:
    """Multiply two numbers as bytes.

    Produces left * right, where left and right are interpreted as big-endian unsigned integers.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_mul, TealType.bytes, TealType.bytes, left, right)


def BytesMod(left: Expr, right: Expr) -> Expr:
    """Modulo expression with bytes as arguments.

    Produces left % right, where left and right are interpreted as big-endian unsigned integers.
    Arguments must not exceed 64 bytes.

    Panics if right is 0.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_mod, TealType.bytes, TealType.bytes, left, right)


def BytesAnd(left: Expr, right: Expr) -> Expr:
    """Bitwise and expression with bytes as arguments.

    Produces left & right.
    Left and right are zero-left extended to the greater of their lengths.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_and, TealType.bytes, TealType.bytes, left, right)


def BytesOr(left: Expr, right: Expr) -> Expr:
    """Bitwise or expression with bytes as arguments.

    Produces left | right.
    Left and right are zero-left extended to the greater of their lengths.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_or, TealType.bytes, TealType.bytes, left, right)


def BytesXor(left: Expr, right: Expr) -> Expr:
    """Bitwise xor expression with bytes as arguments.

    Produces left ^ right.
    Left and right are zero-left extended to the greater of their lengths.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_xor, TealType.bytes, TealType.bytes, left, right)


def BytesEq(left: Expr, right: Expr) -> Expr:
    """Equality expression with bytes as arguments.

    Checks if left == right, where left and right are interpreted as big-endian unsigned integers.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_eq, TealType.bytes, TealType.uint64, left, right)


def BytesNeq(left: Expr, right: Expr) -> Expr:
    """Difference expression with bytes as arguments.

    Checks if left != right, where left and right are interpreted as big-endian unsigned integers.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_neq, TealType.bytes, TealType.uint64, left, right)


def BytesLt(left: Expr, right: Expr) -> Expr:
    """Less than expression with bytes as arguments.

    Checks if left < right, where left and right are interpreted as big-endian unsigned integers.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_lt, TealType.bytes, TealType.uint64, left, right)


def BytesLe(left: Expr, right: Expr) -> Expr:
    """Less than or equal to expression with bytes as arguments.

    Checks if left <= right, where left and right are interpreted as big-endian unsigned integers.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_le, TealType.bytes, TealType.uint64, left, right)


def BytesGt(left: Expr, right: Expr) -> Expr:
    """Greater than expression with bytes as arguments.

    Checks if left > right, where left and right are interpreted as big-endian unsigned integers.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_gt, TealType.bytes, TealType.uint64, left, right)


def BytesGe(left: Expr, right: Expr) -> Expr:
    """Greater than or equal to expression with bytes as arguments.

    Checks if left >= right, where left and right are interpreted as big-endian unsigned integers.
    Arguments must not exceed 64 bytes.

    Requires program version 4 or higher.

    Args:
        left: Must evaluate to bytes.
        right: Must evaluate to bytes.
    """
    return BinaryExpr(Op.b_ge, TealType.bytes, TealType.uint64, left, right)


def ExtractUint16(string: Expr, offset: Expr) -> Expr:
    """Extract 2 bytes (16 bits) and convert them to an integer.

    The bytes starting at :code:`offset` up to but not including :code:`offset + 2` will be
    interpreted as a big-endian unsigned integer.

    If :code:`offset + 2` exceeds :code:`Len(string)`, the program fails.

    Requires program version 5 or higher.

    Args:
        string: The bytestring to extract from. Must evaluate to bytes.
        offset: The offset in the bytestring to start extracing. Must evaluate to uint64.
    """
    return BinaryExpr(
        Op.extract_uint16,
        (TealType.bytes, TealType.uint64),
        TealType.uint64,
        string,
        offset,
    )


def ExtractUint32(string: Expr, offset: Expr) -> Expr:
    """Extract 4 bytes (32 bits) and convert them to an integer.

    The bytes starting at :code:`offset` up to but not including :code:`offset + 4` will be
    interpreted as a big-endian unsigned integer.

    If :code:`offset + 4` exceeds :code:`Len(string)`, the program fails.

    Requires program version 5 or higher.

    Args:
        string: The bytestring to extract from. Must evaluate to bytes.
        offset: The offset in the bytestring to start extracing. Must evaluate to uint64.
    """
    return BinaryExpr(
        Op.extract_uint32,
        (TealType.bytes, TealType.uint64),
        TealType.uint64,
        string,
        offset,
    )


def ExtractUint64(string: Expr, offset: Expr) -> Expr:
    """Extract 8 bytes (64 bits) and convert them to an integer.

    The bytes starting at :code:`offset` up to but not including :code:`offset + 8` will be
    interpreted as a big-endian unsigned integer.

    If :code:`offset + 8` exceeds :code:`Len(string)`, the program fails.

    Requires program version 5 or higher.

    Args:
        string: The bytestring to extract from. Must evaluate to bytes.
        offset: The offset in the bytestring to start extracing. Must evaluate to uint64.
    """
    return BinaryExpr(
        Op.extract_uint64,
        (TealType.bytes, TealType.uint64),
        TealType.uint64,
        string,
        offset,
    )
