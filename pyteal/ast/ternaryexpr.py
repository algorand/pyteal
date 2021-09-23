from typing import Tuple, TYPE_CHECKING

from ..types import TealType, require_type
from ..errors import verifyTealVersion
from ..ir import TealOp, Op, TealBlock
from .expr import Expr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


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
        require_type(firstArg.type_of(), inputTypes[0])
        require_type(secondArg.type_of(), inputTypes[1])
        require_type(thirdArg.type_of(), inputTypes[2])

        self.op = op
        self.outputType = outputType
        self.firstArg = firstArg
        self.secondArg = secondArg
        self.thirdArg = thirdArg

    def __teal__(self, options: "CompileOptions"):
        verifyTealVersion(
            self.op.min_version,
            options.version,
            "TEAL version too low to use op {}".format(self.op),
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
        data: The data signed by the public key. Must evalutes to bytes.
        sig: The proposed 64-byte signature of the concatenation ("ProgData" + hash_of_current_program + data).
            Must evalute to bytes.
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


def Substring(string: Expr, start: Expr, end: Expr) -> TernaryExpr:
    """Take a substring of a byte string.

    Produces a new byte string consisting of the bytes starting at :code:`start` up to but not
    including :code:`end`.

    This expression is similar to :any:`Extract`, except this expression uses start and end indexes,
    while :code:`Extract` uses a start index and length.

    Args:
        string: The byte string.
        start: The starting index for the substring. Must be an integer less than or equal to
            :code:`Len(string)`.
        end: The ending index for the substring. Must be an integer greater or equal to start, but
            less than or equal to Len(string).
    """
    return TernaryExpr(
        Op.substring3,
        (TealType.bytes, TealType.uint64, TealType.uint64),
        TealType.bytes,
        string,
        start,
        end,
    )


def Extract(string: Expr, start: Expr, length: Expr) -> TernaryExpr:
    """Extract a section of a byte string.

    Produces a new byte string consisting of the bytes starting at :code:`start` up to but not
    including :code:`start + length`.

    This expression is similar to :any:`Substring`, except this expression uses a start index and
    length, while :code:`Substring` uses start and end indexes.

    Requires TEAL version 5 or higher.

    Args:
        string: The byte string.
        start: The starting index for the extraction. Must be an integer less than or equal to
            :code:`Len(string)`.
        length: The number of bytes to extract. Must be an integer such that :code:`start + length <= Len(string)`.
    """
    return TernaryExpr(
        Op.extract3,
        (TealType.bytes, TealType.uint64, TealType.uint64),
        TealType.bytes,
        string,
        start,
        length,
    )


def SetBit(value: Expr, index: Expr, newBitValue: Expr) -> TernaryExpr:
    """Set the bit value of an expression at a specific index.

    The meaning of index differs if value is an integer or a byte string.

    * For integers, bit indexing begins with low-order bits. For example, :code:`SetBit(Int(0), Int(4), Int(1))`
      yields the integer 16 (2^4). Any integer less than 64 is a valid index.

    * For byte strings, bit indexing begins at the first byte. For example, :code:`SetBit(Bytes("base16", "0x00"), Int(7), Int(1))`
      yields the byte string 0x01. Any integer less than 8*Len(value) is a valid index.

    Requires TEAL version 3 or higher.

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

    Requires TEAL version 3 or higher.

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
