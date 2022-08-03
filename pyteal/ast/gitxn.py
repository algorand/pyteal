from typing import TYPE_CHECKING, cast, Union

from pyteal.config import MAX_GROUP_SIZE

from pyteal.errors import TealInputError, verifyFieldVersion, verifyProgramVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.expr import Expr
from pyteal.ast.txn import TxnExpr, TxnField, TxnObject, TxnaExpr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class GitxnExpr(TxnExpr):
    """An expression that accesses an inner transaction field from an inner transaction in the last inner group."""

    def __init__(self, txnIndex: int, field: TxnField) -> None:
        super().__init__(Op.gitxn, "Gitxn", field)

        # Currently we do not have gitxns. Only gitxn with immediate transaction index supported.
        if type(txnIndex) is not int:
            raise TealInputError(
                "Invalid gitxn syntax with immediate transaction field {} and transaction index {}".format(
                    field, txnIndex
                )
            )

        self.txnIndex = txnIndex

    def __str__(self):
        return "({} {} {})".format(self.name, self.txnIndex, self.field.arg_name)

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(self.field.arg_name, self.field.min_version, options.version)

        verifyProgramVersion(
            Op.gitxn.min_version,
            options.version,
            "Program version too low to use gitxn",
        )
        op = TealOp(self, Op.gitxn, self.txnIndex, self.field.arg_name)
        return TealBlock.FromOp(options, op)


GitxnExpr.__module__ = "pyteal"


class GitxnaExpr(TxnaExpr):
    """An expression that accesses an inner transaction array field from an inner transaction in the last inner group."""

    def __init__(self, txnIndex: int, field: TxnField, index: Union[int, Expr]) -> None:
        super().__init__(Op.gitxna, Op.gitxnas, "Gitxna", field, index)

        if type(txnIndex) is not int:
            raise TealInputError(
                f"Invalid txnIndex type:  Expected int, but received {txnIndex}."
            )

        self.txnIndex = txnIndex

    def __str__(self):
        return "({} {} {} {})".format(
            self.name, self.txnIndex, self.field.arg_name, self.index
        )

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(self.field.arg_name, self.field.min_version, options.version)

        if type(self.index) is int:
            opToUse = Op.gitxna
        else:
            opToUse = Op.gitxnas

        verifyProgramVersion(
            opToUse.min_version,
            options.version,
            "Program version too low to use op {}".format(opToUse),
        )

        if type(self.index) is int:
            op = TealOp(self, opToUse, self.txnIndex, self.field.arg_name, self.index)
            return TealBlock.FromOp(options, op)
        op = TealOp(self, opToUse, self.txnIndex, self.field.arg_name)
        return TealBlock.FromOp(options, op, cast(Expr, self.index))


GitxnaExpr.__module__ = "pyteal"


class InnerTxnGroup:
    """Represents a group of inner transactions."""

    def __getitem__(self, txnIndex: int) -> TxnObject:
        if type(txnIndex) is not int:
            raise TealInputError(
                "Invalid gitxn syntax, immediate txn index must be int."
            )

        if txnIndex < 0 or txnIndex >= MAX_GROUP_SIZE:
            raise TealInputError(
                "Invalid Gtxn index {}, should be in [0, {})".format(
                    txnIndex, MAX_GROUP_SIZE
                )
            )

        return TxnObject(
            lambda field: GitxnExpr(txnIndex, field),
            lambda field, index: GitxnaExpr(txnIndex, field, index),
        )


InnerTxnGroup.__module__ = "pyteal"

Gitxn: InnerTxnGroup = InnerTxnGroup()

Gitxn.__module__ = "pyteal"
