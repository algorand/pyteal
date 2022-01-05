from typing import TYPE_CHECKING, cast

from pyteal.config import MAX_GROUP_SIZE

from ..errors import TealInputError, verifyFieldVersion, verifyTealVersion
from ..ir import TealOp, Op, TealBlock
from .txn import TxnExpr, TxnField, TxnObject, TxnaExpr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class GitxnExpr(TxnExpr):
    """An expression that accesses an inner transaction field from an inner transaction in the last inner group."""

    def __init__(self, txnIndex: int, field: TxnField) -> None:
        super().__init__(Op.gitxn, "Gitxn", field)
        self.txnIndex = txnIndex

    def __str__(self):
        return "({} {} {})".format(self.name, self.txnIndex, self.field.arg_name)

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(self.field.arg_name, self.field.min_version, options.version)

        # currently we do not have gitxns, only gitxn with immediate transaction index supported
        if type(self.txnIndex) is not int:
            raise TealInputError(
                "Invalid gitxn syntax with immediate transaction field {} and transaction index {}".format(
                    self.field, self.txnIndex
                )
            )

        verifyTealVersion(
            Op.gitxn.min_version,
            options.version,
            "TEAL version too low to use gitxn",
        )
        op = TealOp(self, Op.gitxn, self.txnIndex, self.field.arg_name)
        return TealBlock.FromOp(options, op)


GitxnExpr.__module__ = "pyteal"


class GitxnaExpr(TxnaExpr):
    """An expression that accesses an inner transaction array field from an inner transaction in the last inner group."""

    def __init__(self, txnIndex: int, field: TxnField, index: int) -> None:
        super().__init__(Op.gitxna, None, "Gitxna", field, index)
        self.txnIndex = txnIndex

    def __str__(self):
        return "({} {} {} {})".format(
            self.name, self.txnIndex, self.field.arg_name, self.index
        )

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(self.field.arg_name, self.field.min_version, options.version)
        if type(self.txnIndex) is not int or type(self.index) is not int:
            raise TealInputError(
                "Invalid gitxna syntax with immediate transaction index {}, transaction field {}, array index {}".format(
                    self.txnIndex, self.field, self.index
                )
            )

        verifyTealVersion(
            Op.gitxna.min_version, options.version, "TEAL version too low to use gitxna"
        )
        op = TealOp(self, Op.gitxna, self.txnIndex, self.field.arg_name, self.index)
        return TealBlock.FromOp(options, op)


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
                "Invalid Gtxn index {}, shoud be in [0, {})".format(
                    txnIndex, MAX_GROUP_SIZE
                )
            )

        return TxnObject(
            lambda field: GitxnExpr(txnIndex, field),
            lambda field, index: GitxnaExpr(txnIndex, field, cast(int, index)),
        )


InnerTxnGroup.__module__ = "pyteal"

Gitxn: InnerTxnGroup = InnerTxnGroup()

Gitxn.__module__ = "pyteal"
