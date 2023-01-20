from typing import cast, Union, TYPE_CHECKING

from pyteal.types import TealType, require_type
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.errors import TealInputError, verifyProgramVersion
from pyteal.config import MAX_GROUP_SIZE
from pyteal.ast.expr import Expr
from pyteal.ast.leafexpr import LeafExpr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class GeneratedID(LeafExpr):
    """An expression to obtain the ID of an asset or application created by another transaction in the current group."""

    def __init__(self, txnIndex: Union[int, Expr]) -> None:
        """Create an expression to extract the created ID from a transaction in the current group.

        Requires program version 4 or higher. This operation is only permitted in application mode.

        Args:
            txnIndex: The index of the transaction from which the created ID should be obtained.
                This index may be a Python int, or it may be a PyTeal expression that evaluates at runtime.
                If it's an expression, it must evaluate to a uint64.
                In all cases, the index must be less than the index of the current transaction.
        """
        super().__init__()
        if type(txnIndex) is int:
            if txnIndex < 0 or txnIndex >= MAX_GROUP_SIZE:
                raise TealInputError(
                    "Invalid transaction index {}, shoud be in [0, {})".format(
                        txnIndex, MAX_GROUP_SIZE
                    )
                )
        else:
            require_type(cast(Expr, txnIndex), TealType.uint64)
        self.txnIndex = txnIndex

    def __str__(self):
        return "(Gaid {})".format(self.txnIndex)

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            Op.gaid.min_version,
            options.version,
            "Program version too low to use Gaid expression",
        )

        if type(self.txnIndex) is int:
            op = TealOp(self, Op.gaid, self.txnIndex)
            return TealBlock.FromOp(options, op)

        op = TealOp(self, Op.gaids)
        return TealBlock.FromOp(options, op, cast(Expr, self.txnIndex))

    def type_of(self):
        return TealType.uint64


GeneratedID.__module__ = "pyteal"
