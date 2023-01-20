from typing import Tuple, TYPE_CHECKING

from pyteal.types import TealType, require_type
from pyteal.errors import verifyProgramVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class TernaryExpr(Expr):
    """An expression with three arguments."""

    def __init__(
        self,
        op: Op,
        inputTypes: Tuple[TealType, TealType, TealType],
        outputType: TealType,
        firstArg: Expr,
        secondArg: Expr,
        thirdArg: Expr,
    ) -> None:
        super().__init__()
        require_type(firstArg, inputTypes[0])
        require_type(secondArg, inputTypes[1])
        require_type(thirdArg, inputTypes[2])

        self.op = op
        self.outputType = outputType
        self.firstArg = firstArg
        self.secondArg = secondArg
        self.thirdArg = thirdArg

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            self.op.min_version,
            options.version,
            "Program version too low to use op {}".format(self.op),
        )

        return TealBlock.FromOp(
            options, TealOp(self, self.op), self.firstArg, self.secondArg, self.thirdArg
        )

    def __str__(self):
        return "({} {} {} {})".format(
            self.op, self.firstArg, self.secondArg, self.thirdArg
        )

    def type_of(self):
        return self.outputType

    def has_return(self):
        return False


TernaryExpr.__module__ = "pyteal"


def Ed25519Verify(data: Expr, sig: Expr, key: Expr) -> TernaryExpr:
    """Verify the ed25519 signature of the concatenation ("ProgData" + hash_of_current_program + data).

    Args:
        data: The data signed by the public key. Must evaluate to bytes.
        sig: The proposed 64-byte signature of the concatenation ("ProgData" + hash_of_current_program + data).
            Must evaluate to bytes.
        key: The 32 byte public key that produced the signature. Must evaluate to bytes.
    """
    return TernaryExpr(
        Op.ed25519verify,
        (TealType.bytes, TealType.bytes, TealType.bytes),
        TealType.uint64,
        data,
        sig,
        key,
    )


def Ed25519Verify_Bare(data: Expr, sig: Expr, key: Expr) -> TernaryExpr:
    """Verify the ed25519 signature of the data against the public key.

    Args:
        data: The data signed by the public key. Must evaluate to bytes.
        sig: The proposed 64-byte signature of the data. Must evaluate to bytes.
        key: The 32 byte public key that produced the signature. Must evaluate to bytes.
    """
    return TernaryExpr(
        Op.ed25519verify_bare,
        (TealType.bytes, TealType.bytes, TealType.bytes),
        TealType.uint64,
        data,
        sig,
        key,
    )


def SetBit(value: Expr, index: Expr, newBitValue: Expr) -> TernaryExpr:
    """Set the bit value of an expression at a specific index.

    The meaning of index differs if value is an integer or a byte string.

    * For integers, bit indexing begins with low-order bits. For example, :code:`SetBit(Int(0), Int(4), Int(1))`
      yields the integer 16 (2^4). Any integer less than 64 is a valid index.

    * For byte strings, bit indexing begins at the first byte. For example, :code:`SetBit(Bytes("base16", "0x00"), Int(7), Int(1))`
      yields the byte string 0x01. Any integer less than 8*Len(value) is a valid index.

    Requires program version 3 or higher.

    Args:
        value: The value containing bits. Can evaluate to any type.
        index: The index of the bit to set. Must evaluate to uint64.
        newBitValue: The new bit value to set. Must evaluate to the integer 0 or 1.
    """
    return TernaryExpr(
        Op.setbit,
        (TealType.anytype, TealType.uint64, TealType.uint64),
        value.type_of(),
        value,
        index,
        newBitValue,
    )


def SetByte(value: Expr, index: Expr, newByteValue: Expr) -> TernaryExpr:
    """Set a single byte in a byte string from an integer value.

    Similar to SetBit, indexing begins at the first byte. For example, :code:`SetByte(Bytes("base16", "0x000000"), Int(0), Int(255))`
    yields the byte string 0xff0000.

    Requires program version 3 or higher.

    Args:
        value: The value containing the bytes. Must evaluate to bytes.
        index: The index of the byte to set. Must evaluate to an integer less than Len(value).
        newByteValue: The new byte value to set. Must evaluate to an integer less than 256.
    """
    return TernaryExpr(
        Op.setbyte,
        (TealType.bytes, TealType.uint64, TealType.uint64),
        TealType.bytes,
        value,
        index,
        newByteValue,
    )


def Divw(hi: Expr, lo: Expr, y: Expr) -> TernaryExpr:
    """
    Performs wide division by interpreting `hi` and `lo` as a uint128 value.

    Requires program version 6 or higher.

    Args:
        hi: Quotient's high 64 bits.  Must evaluate to uint64.
        lo: Quotient's low 64 bits.  Must evaluate to uint64.
        y: Divisor.  Must evaluate to uint64.

    """
    return TernaryExpr(
        Op.divw,
        (TealType.uint64, TealType.uint64, TealType.uint64),
        TealType.uint64,
        hi,
        lo,
        y,
    )
