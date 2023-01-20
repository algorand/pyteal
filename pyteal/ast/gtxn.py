from typing import Union, cast, TYPE_CHECKING

from pyteal.types import TealType, require_type
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.errors import TealInputError, verifyFieldVersion, verifyProgramVersion
from pyteal.config import MAX_GROUP_SIZE
from pyteal.ast.expr import Expr
from pyteal.ast.txn import TxnField, TxnExpr, TxnaExpr, TxnObject

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


def validate_txn_index_or_throw(txnIndex: Union[int, Expr]):
    if not isinstance(txnIndex, (int, Expr)):
        raise TealInputError(
            f"Invalid txnIndex type:  Expected int or Expr, but received {txnIndex}"
        )
    if isinstance(txnIndex, Expr):
        require_type(txnIndex, TealType.uint64)


class GtxnExpr(TxnExpr):
    """An expression that accesses a transaction field from a transaction in the current group."""

    def __init__(self, txnIndex: Union[int, Expr], field: TxnField) -> None:
        super().__init__(Op.gtxn, "Gtxn", field)
        validate_txn_index_or_throw(txnIndex)
        self.txnIndex = txnIndex

    def __str__(self):
        return "({} {} {})".format(self.name, self.txnIndex, self.field.arg_name)

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(self.field.arg_name, self.field.min_version, options.version)

        if type(self.txnIndex) is int:
            verifyProgramVersion(
                Op.gtxn.min_version,
                options.version,
                "Program version too low to use gtxn",
            )
            op = TealOp(self, Op.gtxn, self.txnIndex, self.field.arg_name)
            return TealBlock.FromOp(options, op)

        verifyProgramVersion(
            Op.gtxns.min_version,
            options.version,
            "Program version too low to index Gtxn with dynamic values",
        )

        op = TealOp(self, Op.gtxns, self.field.arg_name)
        return TealBlock.FromOp(options, op, cast(Expr, self.txnIndex))


GtxnExpr.__module__ = "pyteal"


class GtxnaExpr(TxnaExpr):
    """An expression that accesses a transaction array field from a transaction in the current group."""

    def __init__(
        self, txnIndex: Union[int, Expr], field: TxnField, index: Union[int, Expr]
    ) -> None:
        super().__init__(Op.gtxna, Op.gtxnas, "Gtxna", field, index)
        validate_txn_index_or_throw(txnIndex)
        self.txnIndex = txnIndex

    def __str__(self):
        return "({} {} {} {})".format(
            self.name, self.txnIndex, self.field.arg_name, self.index
        )

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(self.field.arg_name, self.field.min_version, options.version)

        if type(self.txnIndex) is int:
            if type(self.index) is int:
                opToUse = Op.gtxna
            else:
                opToUse = Op.gtxnas
        else:
            if type(self.index) is int:
                opToUse = Op.gtxnsa
            else:
                opToUse = Op.gtxnsas

        verifyProgramVersion(
            opToUse.min_version,
            options.version,
            "Program version too low to use op {}".format(opToUse),
        )

        if type(self.txnIndex) is int:
            if type(self.index) is int:
                op = TealOp(
                    self, opToUse, self.txnIndex, self.field.arg_name, self.index
                )
                return TealBlock.FromOp(options, op)
            op = TealOp(self, opToUse, self.txnIndex, self.field.arg_name)
            return TealBlock.FromOp(options, op, cast(Expr, self.index))

        if type(self.index) is int:
            op = TealOp(self, opToUse, self.field.arg_name, self.index)
            return TealBlock.FromOp(options, op, cast(Expr, self.txnIndex))

        op = TealOp(self, opToUse, self.field.arg_name)
        return TealBlock.FromOp(
            options, op, cast(Expr, self.txnIndex), cast(Expr, self.index)
        )


GtxnaExpr.__module__ = "pyteal"


class TxnGroup:
    """Represents a group of transactions."""

    def __getitem__(self, txnIndex: Union[int, Expr]) -> TxnObject:
        if type(txnIndex) is int:
            if txnIndex < 0 or txnIndex >= MAX_GROUP_SIZE:
                raise TealInputError(
                    "Invalid Gtxn index {}, shoud be in [0, {})".format(
                        txnIndex, MAX_GROUP_SIZE
                    )
                )
        else:
            require_type(cast(Expr, txnIndex), TealType.uint64)
        return TxnObject(
            lambda field: GtxnExpr(txnIndex, field),
            lambda field, index: GtxnaExpr(txnIndex, field, index),
        )


TxnGroup.__module__ = "pyteal"

Gtxn: TxnGroup = TxnGroup()

Gtxn.__module__ = "pyteal"
