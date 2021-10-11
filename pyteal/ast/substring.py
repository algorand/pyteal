from enum import Enum
from typing import Tuple, TYPE_CHECKING

from ..types import TealType, require_type
from ..errors import verifyTealVersion
from ..ir import TealOp, Op, TealBlock, TealSimpleBlock
from .expr import Expr
from .int import Int
from .ternaryexpr import TernaryExpr

if TYPE_CHECKING:
    from ..compiler import CompileOptions

class SubstringExpr(Expr):
    def __init__(
        self,
        stringArg: Expr,
        startArg: Expr,
        endArg: Expr
    ) -> None:
        super().__init__()

        require_type(stringArg.type_of(), TealType.bytes)
        require_type(startArg.type_of(), TealType.uint64)
        require_type(endArg.type_of(), TealType.uint64)

        self.stringArg = stringArg
        self.startArg = startArg
        self.endArg = endArg

    # helper methods for correctly populating self.op
    def __setOp(self, options: "CompileOptions"):
        s, e = self.startArg.value, self.endArg.value
        l = e - s
        if options.version >= Op.extract.min_version:
            if s < 2 ** 8 and l < 2 ** 8:
                self.op = Op.extract
            else:
                self.op = Op.extract3
        else:
            if s < 2 ** 8 and e < 2 ** 8:
                self.op = Op.substring
            else:
                self.op = Op.substring3

    def __teal__(self, options: "CompileOptions"):
        if isinstance(self.startArg, Int) and isinstance(self.endArg, Int):
            self.__setOp(options)
        else:
            return TernaryExpr(
                Op.substring3,
                (TealType.bytes, TealType.uint64, TealType.uint64),
                TealType.bytes,
                self.stringArg,
                self.startArg,
                self.endArg,
            ).__teal__(options)

        verifyTealVersion(
            self.op.min_version,
            options.version,
            "TEAL version too low to use op {}".format(self.op),
        )

        if self.op == Op.extract:
            length = self.endArg.value - self.startArg.value
            return TealBlock.FromOp(
                options, TealOp(self, self.op, self.startArg.value, length), self.stringArg
            )
        elif self.op == Op.extract3:
            length = self.endArg.value - self.startArg.value
            return TealBlock.FromOp(
                options, TealOp(self, self.op), self.stringArg, self.startArg, Int(length)
            )
        elif self.op == Op.substring:
            return TealBlock.FromOp(
                options, TealOp(self, self.op, self.startArg.value, self.endArg.value), self.stringArg
            )
        elif self.op == Op.substring3:
            return TealBlock.FromOp(
                options, TealOp(self, self.op), self.stringArg, self.startArg, self.endArg
            )

    def __str__(self):
        return "({} {} {} {})".format(
            self.op, self.stringArg, self.startArg, self.endArg
        )

    def type_of(self):
        return TealType.bytes

    def has_return(self):
        return False


class ExtractExpr(Expr):
    """For optimization using immediate args when index values can each be stored in one byte"""
    """An expression with three arguments."""

    def __init__(
        self,
        stringArg: Expr,
        startArg: Expr,
        lenArg: Expr
    ) -> None:
        super().__init__()

        require_type(stringArg.type_of(), TealType.bytes)
        require_type(startArg.type_of(), TealType.uint64)
        require_type(lenArg.type_of(), TealType.uint64)

        self.stringArg = stringArg
        self.startArg = startArg
        self.lenArg = lenArg

    # helper methods for correctly populating self.op
    def __setOp(self, options: "CompileOptions"):
        s, l = self.startArg.value, self.lenArg.value
        if s < 2 ** 8 and l > 0 and l < 2 ** 8:
            self.op = Op.extract
        else:
            self.op = Op.extract3

    def __teal__(self, options: "CompileOptions"):
        if isinstance(self.startArg, Int) and isinstance(self.lenArg, Int):
            self.__setOp(options)
        else:
            return TernaryExpr(
                Op.extract3,
                (TealType.bytes, TealType.uint64, TealType.uint64),
                TealType.bytes,
                self.stringArg,
                self.startArg,
                self.lenArg,
            ).__teal__(options)

        verifyTealVersion(
            self.op.min_version,
            options.version,
            "TEAL version too low to use op {}".format(self.op),
        )

        if self.op == Op.extract:
            return TealBlock.FromOp(
                options, TealOp(self, self.op, self.startArg.value, self.lenArg.value), self.stringArg
            )
        elif self.op == Op.extract3:
            return TealBlock.FromOp(
                options, TealOp(self, self.op), self.stringArg, self.startArg, self.lenArg
            )

    def __str__(self):
        return "({} {} {} {})".format(
            self.op, self.stringArg, self.startArg, self.lenArg
        )

    def type_of(self):
        return TealType.bytes

    def has_return(self):
        return False


class SuffixExpr(Expr):
    """For optimization using immediate args when index values can each be stored in one byte"""
    """An expression with three arguments."""

    def __init__(
        self,
        stringArg: Expr,
        startArg: Expr,
    ) -> None:
        super().__init__()

        require_type(stringArg.type_of(), TealType.bytes)
        require_type(startArg.type_of(), TealType.uint64)

        self.stringArg = stringArg
        self.startArg = startArg

    # helper methods for correctly populating self.op
    def __setOp(self, options: "CompileOptions"):
        if not isinstance(self.startArg, Int):
            self.op = Op.substring3
            return

        s = self.startArg.value
        if s < 2 ** 8:
            self.op = Op.extract
        else:
            self.op = Op.substring3

    def __teal__(self, options: "CompileOptions"):
        self.__setOp(options)

        verifyTealVersion(
            self.op.min_version,
            options.version,
            "TEAL version too low to use op {}".format(self.op),
        )

        if self.op == Op.extract:
            return TealBlock.FromOp(
                options, TealOp(self, self.op, self.startArg.value, 0), self.stringArg
            )
        elif self.op == Op.substring3:
            strBlockStart, strBlockEnd = self.stringArg.__teal__(options)
            nextBlockStart, nextBlockEnd = self.startArg.__teal__(options)
            strBlockEnd.setNextBlock(nextBlockStart)
            
            finalBlock = TealSimpleBlock(
                [
                    TealOp(..., Op.dig, 1),
                    TealOp(..., Op.len),
                    TealOp(..., Op.substring3),
                ]
            )
            
            nextBlockEnd.setNextBlock(finalBlock)
            return strBlockStart, finalBlock

    def __str__(self):
        return "({} {} {} {})".format(
            self.op, self.stringArg, self.startArg
        )

    def type_of(self):
        return TealType.bytes

    def has_return(self):
        return False


def Substring(string: Expr, start: Expr, end: Expr) -> Expr:
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
    return SubstringExpr(
        string,
        start,
        end,
    )


def Extract(string: Expr, start: Expr, length: Expr) -> Expr:
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
    return ExtractExpr(
        string,
        start,
        length,
    )


def Suffix(string: Expr, start: Expr) -> Expr:
    """Take a suffix of a byte string.

    Produces a new byte string consisting of the suffix of the byte string starting at :code:`start`

    This expression is similar to :any:`Substring` and :any:`Extract`, except this expression only uses a
    start index.

    Requires TEAL version 5 or higher.

    Args:
        string: The byte string.
        start: The starting index for the suffix. Must be an integer less than or equal to :code:`Len(string)`.
    """
    return SuffixExpr(
        string,
        start,
    )