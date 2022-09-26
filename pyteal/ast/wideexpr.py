from typing import TYPE_CHECKING, List

from pyteal.ast.expr import Expr
from pyteal.ast.multi import MultiValue
from pyteal.errors import verifyProgramVersion
from pyteal.ir import Op
from pyteal.types import TealType, require_type

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class WideExpr(MultiValue):
    """Base class for WideInt Operations

    This type of expression produces WideInt(MultiValue).
    """

    def __init__(
        self,
        op: Op,
        args: List[Expr],
    ):
        """Create a new WideExpr, whose returned type is always a MultiValue of [TealType.uint64, TealType.uint64].

        Args:
            op: The operation that returns values.
            args: Stack arguments for the op.
            min_version: The minimum TEAL version required to use this expression.
        """

        super().__init__(
            op=op,
            types=[TealType.uint64, TealType.uint64],
            args=args,
            immediate_args=None,
        )

        for arg in args:
            require_type(arg, TealType.uint64)

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            self.op.min_version,
            options.version,
            "Program version too low to use op {}".format(self.op),
        )

        return super().__teal__(options)


WideExpr.__module__ = "pyteal"

"""Binary MultiValue operations"""


def AddW(adder: Expr, adder_: Expr) -> MultiValue:
    """Add two 64-bit integers.

    Produces a MultiValue with two outputs: the sum and the carry-bit.

    Args:
        adder: Must evaluate to uint64.
        adder_: Must evaluate to uint64.
    """
    return WideExpr(Op.addw, [adder, adder_])


def MulW(factor: Expr, factor_: Expr) -> MultiValue:
    """Multiply two 64-bit integers.

    Produces a MultiValue with two outputs: the product and the carry-bit.

    Args:
        factor: Must evaluate to uint64.
        factor_: Must evaluate to uint64.
    """

    return WideExpr(Op.mulw, [factor, factor_])


def ExpW(base: Expr, exponent: Expr) -> MultiValue:
    """Raise a 64-bit integer to a power.

    Produces a MultiValue with two outputs: the result and the carry-bit.

    Args:
        base: Must evaluate to uint64.
        exponent: Must evaluate to uint64.
    """

    return WideExpr(Op.expw, [base, exponent])


def DivModW(
    dividendHigh: Expr, dividendLow: Expr, divisorHigh: Expr, divisorLow: Expr
) -> MultiValue:
    """Divide two wide-64-bit integers.

    Produces a MultiValue with four outputs: the quotient and its carry-bit, the remainder and its carry-bit.

    Stack:
        ..., A: uint64, B: uint64, C: uint64, D: uint64 --> ..., W: uint64, X: uint64, Y: uint64, Z: uint64
        Where W,X = (A,B / C,D); Y,Z = (A,B modulo C,D)

    Example:
        All ints should be initialized with Int(). For readability, we didn't use Int() in the example.
        DivModW(0, 10, 0, 5) = (0, 2, 0, 0) # 10 / 5 = 2, 10 % 5 = 0
        DivModW(0, 10, 0, 3) = (0, 3, 0, 1) # 10 / 3 = 3, 10 % 3 = 1
        DivModW(5, 14, 0, 5) = (1, 2, 0, 4) # ((5<<64)+14) / 5 = (1<<64)+2, ((5<<64)+14) % 5 = 4
        DivModW(7, 29, 1, 3) = (0, 7, 0, 8) # ((7<<64)+29) / ((1<<64)+3) = 7, ((7<<64)+29) % ((1<<64)+3) = 8

    Args:
        dividendHigh: Must evaluate to uint64.
        dividendLow: Must evaluate to uint64.
        divisorHigh: Must evaluate to uint64.
        divisorLow: Must evaluate to uint64.
    """

    return WideExpr(
        Op.divmodw,
        [dividendHigh, dividendLow, divisorHigh, divisorLow],
    )
