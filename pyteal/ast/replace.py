from typing import cast, TYPE_CHECKING

from pyteal.types import TealType, require_type
from pyteal.errors import verifyProgramVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from pyteal.ast.ternaryexpr import TernaryExpr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class ReplaceExpr(Expr):
    """An expression for replacing a section of a byte string at a given start index"""

    def __init__(self, original: Expr, start: Expr, replacement: Expr) -> None:
        super().__init__()

        require_type(original, TealType.bytes)
        require_type(start, TealType.uint64)
        require_type(replacement, TealType.bytes)

        self.original = original
        self.start = start
        self.replacement = replacement

    # helper method for correctly populating op
    def __get_op(self, options: "CompileOptions"):
        s = cast(Int, self.start).value
        if s < 2**8:
            return Op.replace2
        else:
            return Op.replace3

    def __teal__(self, options: "CompileOptions"):
        if not isinstance(self.start, Int):
            return TernaryExpr(
                Op.replace3,
                (TealType.bytes, TealType.uint64, TealType.bytes),
                TealType.bytes,
                self.original,
                self.start,
                self.replacement,
            ).__teal__(options)

        op = self.__get_op(options)

        verifyProgramVersion(
            op.min_version,
            options.version,
            "Program version too low to use op {}".format(op),
        )

        s = cast(Int, self.start).value
        if op == Op.replace2:
            return TealBlock.FromOp(
                options, TealOp(self, op, s), self.original, self.replacement
            )
        elif op == Op.replace3:
            return TealBlock.FromOp(
                options, TealOp(self, op), self.original, self.start, self.replacement
            )

    def __str__(self):
        return "(Replace {} {} {})".format(self.original, self.start, self.replacement)

    def type_of(self):
        return TealType.bytes

    def has_return(self):
        return False


def Replace(original: Expr, start: Expr, replacement: Expr) -> Expr:
    """
    Replace a portion of original bytes with new bytes at a given starting point.

    Requires program version 7 or higher.

    Args:
        original: The value containing the original bytes. Must evaluate to bytes.
        start: The index of the byte where replacement starts. Must evaluate to an integer less than Len(original).
        replacement: The value containing the replacement bytes. Must evaluate to bytes with length at most Len(original) - start.
    """
    return ReplaceExpr(original, start, replacement)
