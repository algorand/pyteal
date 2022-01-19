from typing import cast, Union, TYPE_CHECKING

from ..types import TealType, require_type
from ..ir import TealOp, Op, TealBlock
from ..errors import TealInputError, verifyTealVersion
from ..config import MAX_GROUP_SIZE, NUM_SLOTS
from .expr import Expr
from .leafexpr import LeafExpr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class ImportScratchValue(LeafExpr):
    """An expression to load a scratch value created by another transaction in the current group"""

    def __init__(self, txnIndex: Union[int, Expr], slotId: Union[int, Expr]) -> None:
        """Create an expression to load a scratch space slot from a transaction in the current group.

        Requires TEAL version 4 or higher. This operation is only permitted in application mode.

        Args:
            txnIndex: The index of the transaction from which the created ID should be obtained.
                This index may be a Python int, or it may be a PyTeal expression that evaluates at
                runtime. If it's an expression, it must evaluate to a uint64. In all cases, the index
                must be less than the index of the current transaction.
            slotId: The index of the scratch slot that should be loaded.
                This index may be a Python int, or it may be a PyTeal expression that evaluates at
                runtime. If it's an expression, it must evaluate to a uint64. In all cases, the index
                must be in the range [0, 256).
        """
        super().__init__()
        if type(txnIndex) is int:
            if txnIndex < 0 or txnIndex >= MAX_GROUP_SIZE:
                raise TealInputError(
                    "Invalid transaction index {}, shoud be in [0, {})".format(
                        txnIndex, MAX_GROUP_SIZE
                    )
                )
            if type(slotId) is not int:
                raise TealInputError(
                    "Invalid gload syntax with immediate transaction index {} and stack slot ID {}".format(
                        txnIndex, slotId
                    )
                )
        else:
            require_type(cast(Expr, txnIndex), TealType.uint64)

        if type(slotId) is int:
            if slotId < 0 or slotId >= NUM_SLOTS:
                raise TealInputError(
                    "Invalid slot ID {}, shoud be in [0, {})".format(slotId, NUM_SLOTS)
                )
        else:
            require_type(cast(Expr, slotId), TealType.uint64)

        self.txnIndex = txnIndex
        self.slotId = slotId

    def __str__(self) -> str:
        return "(Gload {} {})".format(self.txnIndex, self.slotId)

    def __teal__(self, options: "CompileOptions"):
        def local_version_check(opcode: TealOp):
            verifyTealVersion(
                opcode.op.min_version,
                options.version,
                "TEAL version too low to use {} experssion".format(opcode.op.name),
            )

        # For txnIndex and slotId, there are only three scenario as following
        #     immediate    immediate
        #     stack        immediate
        #     stack        stack
        # the last one is not allowed
        # --> immediate    stack
        # which is eliminated in __init__
        if type(self.txnIndex) is int and type(self.slotId) is int:
            op = TealOp(self, Op.gload, self.txnIndex, self.slotId)
            local_version_check(op)
            return TealBlock.FromOp(options, op)
        elif type(self.slotId) is int:
            op = TealOp(self, Op.gloads, self.slotId)
            local_version_check(op)
            return TealBlock.FromOp(options, op, cast(Expr, self.txnIndex))
        else:
            op = TealOp(self, Op.gloadss)
            local_version_check(op)
            return TealBlock.FromOp(
                options, op, cast(Expr, self.txnIndex), cast(Expr, self.slotId)
            )

    def type_of(self):
        return TealType.anytype


ImportScratchValue.__module__ = "pyteal"
