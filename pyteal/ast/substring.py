from enum import Enum
from typing import cast, Tuple, TYPE_CHECKING

from ..types import TealType, require_type
from ..errors import TealCompileError, verifyTealVersion
from ..ir import TealOp, Op, TealBlock, TealSimpleBlock
from .expr import Expr
from .int import Int
from .ternaryexpr import TernaryExpr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class SubstringExpr(Expr):
    """An expression for taking the substring of a byte string given start and end indices"""

    def __init__(self, stringArg: Expr, startArg: Expr, endArg: Expr) -> None:
        super().__init__()

        require_type(stringArg, TealType.bytes)
        require_type(startArg, TealType.uint64)
        require_type(endArg, TealType.uint64)

        self.stringArg = stringArg
        self.startArg = startArg
        self.endArg = endArg

    # helper method for correctly populating op
    def __getOp(self, options: "CompileOptions"):
        s, e = cast(Int, self.startArg).value, cast(Int, self.endArg).value
        l = e - s

        if l < 0:
            raise TealCompileError(
                "The end index must be greater than or equal to the start index",
                self,
            )

        if l > 0 and options.version >= Op.extract.min_version:
            if s < 2 ** 8 and l < 2 ** 8:
                return Op.extract
            else:
                return Op.extract3
        else:
            if s < 2 ** 8 and e < 2 ** 8:
                return Op.substring
            else:
                return Op.substring3

    def __teal__(self, options: "CompileOptions"):
        if not isinstance(self.startArg, Int) or not isinstance(self.endArg, Int):
            return TernaryExpr(
                Op.substring3,
                (TealType.bytes, TealType.uint64, TealType.uint64),
                TealType.bytes,
                self.stringArg,
                self.startArg,
                self.endArg,
            ).__teal__(options)

        op = self.__getOp(options)

        verifyTealVersion(
            op.min_version,
            options.version,
            "TEAL version too low to use op {}".format(op),
        )

        start, end = cast(Int, self.startArg).value, cast(Int, self.endArg).value
        if op == Op.extract:
            length = end - start
            return TealBlock.FromOp(
                options,
                TealOp(self, op, self.startArg.value, length),
                self.stringArg,
            )
        elif op == Op.extract3:
            length = end - start
            return TealBlock.FromOp(
                options,
                TealOp(self, op),
                self.stringArg,
                self.startArg,
                Int(length),
            )
        elif op == Op.substring:
            return TealBlock.FromOp(
                options, TealOp(self, op, start, end), self.stringArg
            )
        elif op == Op.substring3:
            return TealBlock.FromOp(
                options,
                TealOp(self, op),
                self.stringArg,
                self.startArg,
                self.endArg,
            )

    def __str__(self):
        return "(Substring {} {} {})".format(self.stringArg, self.startArg, self.endArg)

    def type_of(self):
        return TealType.bytes

    def has_return(self):
        return False


class ExtractExpr(Expr):
    """An expression for extracting a section of a byte string given a start index and length"""

    def __init__(self, stringArg: Expr, startArg: Expr, lenArg: Expr) -> None:
        super().__init__()

        require_type(stringArg, TealType.bytes)
        require_type(startArg, TealType.uint64)
        require_type(lenArg, TealType.uint64)

        self.stringArg = stringArg
        self.startArg = startArg
        self.lenArg = lenArg

    # helper method for correctly populating op
    def __getOp(self, options: "CompileOptions"):
        s, l = cast(Int, self.startArg).value, cast(Int, self.lenArg).value
        if s < 2 ** 8 and l > 0 and l < 2 ** 8:
            return Op.extract
        else:
            return Op.extract3

    def __teal__(self, options: "CompileOptions"):
        if not isinstance(self.startArg, Int) or not isinstance(self.lenArg, Int):
            return TernaryExpr(
                Op.extract3,
                (TealType.bytes, TealType.uint64, TealType.uint64),
                TealType.bytes,
                self.stringArg,
                self.startArg,
                self.lenArg,
            ).__teal__(options)

        op = self.__getOp(options)

        verifyTealVersion(
            op.min_version,
            options.version,
            "TEAL version too low to use op {}".format(op),
        )

        s, l = cast(Int, self.startArg).value, cast(Int, self.lenArg).value
        if op == Op.extract:
            return TealBlock.FromOp(options, TealOp(self, op, s, l), self.stringArg)
        elif op == Op.extract3:
            return TealBlock.FromOp(
                options,
                TealOp(self, op),
                self.stringArg,
                self.startArg,
                self.lenArg,
            )

    def __str__(self):
        return "(Extract {} {} {})".format(self.stringArg, self.startArg, self.lenArg)

    def type_of(self):
        return TealType.bytes

    def has_return(self):
        return False


class SuffixExpr(Expr):
    """An expression for taking the suffix of a byte string given start index"""

    def __init__(
        self,
        stringArg: Expr,
        startArg: Expr,
    ) -> None:
        super().__init__()

        require_type(stringArg, TealType.bytes)
        require_type(startArg, TealType.uint64)

        self.stringArg = stringArg
        self.startArg = startArg

    # helper method for correctly populating op
    def __getOp(self, options: "CompileOptions"):
        if not isinstance(self.startArg, Int):
            return Op.substring3

        s = cast(Int, self.startArg).value
        if s < 2 ** 8:
            return Op.extract
        else:
            return Op.substring3

    def __teal__(self, options: "CompileOptions"):
        op = self.__getOp(options)

        verifyTealVersion(
            op.min_version,
            options.version,
            "TEAL version too low to use op {}".format(op),
        )

        if op == Op.extract:
            # if possible, exploit optimization in the extract opcode that takes the suffix
            # when the length argument is 0
            return TealBlock.FromOp(
                options,
                TealOp(self, op, cast(Int, self.startArg).value, 0),
                self.stringArg,
            )
        elif op == Op.substring3:
            strBlockStart, strBlockEnd = self.stringArg.__teal__(options)
            nextBlockStart, nextBlockEnd = self.startArg.__teal__(options)
            strBlockEnd.setNextBlock(nextBlockStart)

            finalBlock = TealSimpleBlock(
                [
                    TealOp(self, Op.dig, 1),
                    TealOp(self, Op.len),
                    TealOp(self, Op.substring3),
                ]
            )

            nextBlockEnd.setNextBlock(finalBlock)
            return strBlockStart, finalBlock

    def __str__(self):
        return "(Suffix {} {})".format(self.stringArg, self.startArg)

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

    Requires TEAL version 2 or higher.

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
