from typing import cast, Union, TYPE_CHECKING

from ..types import TealType, require_type
from ..ir import TealOp, Op, TealBlock
from ..errors import TealInputError, verifyTealVersion
from ..config import MAX_GROUP_SIZE, NUM_SLOTS
from .expr import Expr
from .int import Int
from .leafexpr import LeafExpr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class ImportScratchValue(LeafExpr):
    """An expression to load a scratch value created by another transaction in the current group"""

    def __init__(self, txnIndex: Union[int, Expr], slotId: int) -> None:
        """Create an expression to load a scratch space slot from a transaction in the current group.

        Requires TEAL version 4 or higher. This operation is only permitted in application mode.

        Args:
            txnIndex: The index of the transaction from which the created ID should be obtained.
                This index may be a Python int, or it may be a PyTeal expression that evaluates at
                runtime. If it's an expression, it must evaluate to a uint64. In all cases, the index
                must be less than the index of the current transaction.
            slotId: The index of the scratch slot that should be loaded. The index must be a Python int
                in the range [0-256).
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
            require_type(cast(Expr, txnIndex).type_of(), TealType.uint64)
        if slotId < 0 or slotId >= NUM_SLOTS:
            raise TealInputError(
                "Invalid slot ID {}, shoud be in [0, {})".format(slotId, NUM_SLOTS)
            )

        self.txnIndex = txnIndex
        self.slotId = slotId

    def __str__(self) -> str:
        return "(Gload {} {})".format(self.txnIndex, self.slotId)

    def __teal__(self, options: "CompileOptions"):
        verifyTealVersion(
            Op.gload.min_version,
            options.version,
            "TEAL version too low to use Gload expression",
        )

        if type(self.txnIndex) is int:
            op = TealOp(self, Op.gload, self.txnIndex, self.slotId)
            return TealBlock.FromOp(options, op)

        op = TealOp(self, Op.gloads, self.slotId)
        return TealBlock.FromOp(options, op, cast(Expr, self.txnIndex))

    def type_of(self):
        return TealType.anytype


ImportScratchValue.__module__ = "pyteal"
