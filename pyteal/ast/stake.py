from typing import TYPE_CHECKING

from pyteal.types import TealType
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.errors import verifyProgramVersion
from pyteal.ast.leafexpr import LeafExpr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class OnlineStake(LeafExpr):
    """An expression to obtain the online stake for the agreement round."""

    def __str__(self):
        return "(OnlineStake)"

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            Op.online_stake.min_version,
            options.version,
            "Program version too low to use OnlineStake expression",
        )

        op = TealOp(self, Op.online_stake)
        return TealBlock.FromOp(options, op)

    def type_of(self):
        return TealType.uint64


OnlineStake.__module__ = "pyteal"
