from ..types import TealType
from ..ir import TealOp, Op
from ..errors import TealInputError
from ..config import MAX_GROUP_SIZE
from .expr import Expr
from .leafexpr import LeafExpr
from .txn import TxnField, TxnExpr, TxnaExpr, TxnObject
from .global_ import Global

class GtxnExpr(TxnExpr):
    """An expression that accesses a transaction field from a transaction in the current group."""

    def __init__(self, txnIndex: int, field: TxnField) -> None:
        super().__init__(field)
        self.txnIndex = txnIndex

    def __str__(self):
        return "(Gtxn {} {})".format(self.txnIndex, self.field.arg_name)

    def __teal__(self):
        return [TealOp(Op.gtxn, self.txnIndex, self.field.arg_name)]

GtxnExpr.__module__ = "pyteal"

class GtxnaExpr(TxnaExpr):
    """An expression that accesses a transaction array field from a transaction in the current group."""

    def __init__(self, txnIndex: int, field: TxnField, index: int) -> None:
        super().__init__(field, index)
        self.txnIndex = txnIndex

    def __str__(self):
        return "(Gtxna {} {} {})".format(self.index, self.field.arg_name, self.index)

    def __teal__(self):
        return [TealOp(Op.gtxna, self.txnIndex, self.field.arg_name, self.index)]

GtxnaExpr.__module__ = "pyteal"

class TxnGroup:
    """Represents a group of transactions."""

    def __getitem__(self, txnIndex: int) -> TxnObject:
        if txnIndex < 0 or txnIndex >= MAX_GROUP_SIZE:
            raise TealInputError("Invalid Gtxn index {}, shoud be in [0, {})".format(txnIndex, MAX_GROUP_SIZE))
        return TxnObject(lambda field: GtxnExpr(txnIndex, field), lambda field, index: GtxnaExpr(txnIndex, field, index))

TxnGroup.__module__ = "pyteal"

Gtxn: TxnGroup = TxnGroup()

Gtxn.__module__ = "pyteal"
