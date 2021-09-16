from typing import Dict, Tuple, TYPE_CHECKING

from ..types import TealType, require_type
from ..errors import TealInputError, verifyTealVersion
from ..ir import TealOp, Op, TealBlock
from .expr import Expr
from .txn import TxnField, TxnExprBuilder, TxnaExprBuilder, TxnObject
from .seq import Seq

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class InnerTxnActionExpr(Expr):
    def __init__(self, begin: bool) -> None:
        super().__init__()
        self.begin = begin

    def __str__(self):
        return "(InnerTxn{})".format("Begin" if self.begin else "Submit")

    def __teal__(self, options: "CompileOptions"):
        op = Op.itxn_begin if self.begin else Op.itxn_submit

        verifyTealVersion(
            op.min_version,
            options.version,
            "TEAL version too low to create inner transactions",
        )

        return TealBlock.FromOp(options, TealOp(self, op))

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


class InnerTxnFieldExpr(Expr):
    def __init__(self, field: TxnField, value: Expr) -> None:
        super().__init__()
        if field.is_array:
            raise TealInputError("Unexpected array field: {}".format(field))
        require_type(value.type_of(), field.type_of())
        self.field = field
        self.value = value

    def __str__(self):
        return "(InnerTxnSetField {} {})".format(self.field.arg_name, self.value)

    def __teal__(self, options: "CompileOptions"):
        verifyTealVersion(
            Op.itxn_field.min_version,
            options.version,
            "TEAL version too low to create inner transactions",
        )

        return TealBlock.FromOp(
            options, TealOp(self, Op.itxn_field, self.field.arg_name), self.value
        )

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


class InnerTxnBuilder:
    @classmethod
    def Begin(cls) -> Expr:
        return InnerTxnActionExpr(True)

    @classmethod
    def Submit(cls) -> Expr:
        return InnerTxnActionExpr(False)

    @classmethod
    def SetField(cls, field: TxnField, value: Expr) -> Expr:
        return InnerTxnFieldExpr(field, value)

    @classmethod
    def SetFields(cls, fields: Dict[TxnField, Expr]) -> Expr:
        fieldsToSet = [cls.SetField(field, value) for field, value in fields.items()]
        return Seq(fieldsToSet)


InnerTxnBuilder.__module__ = "pyteal"

InnerTxn: TxnObject = TxnObject(
    TxnExprBuilder(Op.itxn, "InnerTxn"), TxnaExprBuilder(Op.itxna, None, "InnerTxna")
)

InnerTxn.__module__ = "pyteal"
