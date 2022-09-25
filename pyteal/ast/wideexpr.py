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


"""Binary MultiValue operations"""


def AddW(adder: Expr, adder_: Expr) -> MultiValue:
    """Add two 64-bit integers.

    Produces a MultiValue with two outputs: the sum and the carry-bit.

    Args:
        adder: Must evaluate to uint64.
        adder_: Must evaluate to uint64.
    """
    return WideExpr(Op.addw, [adder, adder_])
