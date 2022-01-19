from enum import Enum
from typing import Dict, TYPE_CHECKING, List, Union, cast

from ..types import TealType, require_type
from ..errors import TealInputError, verifyTealVersion
from ..ir import TealOp, Op, TealBlock
from .expr import Expr
from .txn import TxnField, TxnExprBuilder, TxnaExprBuilder, TxnObject
from .seq import Seq

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class InnerTxnAction(Enum):
    Begin = Op.itxn_begin
    Submit = Op.itxn_submit
    Next = Op.itxn_next


InnerTxnAction.__module__ = "pyteal"


class InnerTxnActionExpr(Expr):
    def __init__(self, action: InnerTxnAction) -> None:
        super().__init__()
        self.action = action

    def __str__(self):
        return "(InnerTxn{})".format(self.action.name)

    def __teal__(self, options: "CompileOptions"):
        op = self.action.value

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
        require_type(value, field.type_of())
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
    """This class represents expressions used to create, modify, and submit inner transactions.

    Inner transactions are transactions which applications can dynamically create. Each inner
    transaction will appear as a transaction inside of the current transaction being executed.

    As of TEAL version 5, only the transaction types :any:`TxnType.Payment`, :any:`TxnType.AssetTransfer`,
    :any:`TxnType.AssetConfig`, and :any:`TxnType.AssetFreeze` are allowed. Additionally, not all
    fields are allowed to be set. For example, it is not currently allowed to set the rekeyTo field
    of an inner transaction.
    """

    @classmethod
    def Begin(cls) -> Expr:
        """Begin preparation of a new inner transaction.

        This new inner transaction is initialized with its sender to the application address (:any:`Global.current_application_address`);
        fee to the minimum allowable, taking into account :code:`MinTxnFee` and credit from
        overpaying in earlier transactions; :code:`FirstValid`/:code:`LastValid` to the values in
        the top-level transaction, and all other fields to zero values.

        Requires TEAL version 5 or higher. This operation is only permitted in application mode.
        """
        return InnerTxnActionExpr(InnerTxnAction.Begin)

    @classmethod
    def Next(cls) -> Expr:
        """Begin preparation of a new inner transaction (in the same transaction group).

        This new inner transaction is initialized with its sender to the application address (:any:`Global.current_application_address`);
        fee to the minimum allowable, taking into account :code:`MinTxnFee` and credit from
        overpaying in earlier transactions; :code:`FirstValid`/:code:`LastValid` to the values in
        the top-level transaction, and all other fields to zero values.

        Requires TEAL version 6 or higher. This operation is only permitted in application mode.
        """
        return InnerTxnActionExpr(InnerTxnAction.Next)

    @classmethod
    def Submit(cls) -> Expr:
        """Execute the current inner transaction.

        :any:`InnerTxnBuilder.Begin` and :any:`InnerTxnBuilder.SetField` must be called before
        submitting an inner transaction.

        This will fail fail if 16 inner transactions have already been executed, or if the
        inner transaction itself fails. Upon failure, the current program will immediately exit and
        fail as well.

        If the inner transaction is successful, then its effects can be immediately observed by this
        program with stateful expressions such as :any:`Balance`. Additionally, the fields of the
        most recently submitted inner transaction can be examined using the :any:`InnerTxn` object.
        If the inner transaction creates an asset, the new asset ID can be found by looking at
        :any:`InnerTxn.created_asset_id() <TxnObject.created_asset_id>`.

        Requires TEAL version 5 or higher. This operation is only permitted in application mode.
        """
        return InnerTxnActionExpr(InnerTxnAction.Submit)

    @classmethod
    def SetField(cls, field: TxnField, value: Union[Expr, List[Expr]]) -> Expr:
        """Set a field of the current inner transaction.

        :any:`InnerTxnBuilder.Begin` must be called before setting any fields on an inner
        transaction.

        Note: For non-array field (e.g., note), setting it twice will overwrite the original value.
              While for array field (e.g., accounts), setting it multiple times will append the values.

        Requires TEAL version 5 or higher. This operation is only permitted in application mode.

        Args:
            field: The field to set on the inner transaction.
            value: The value to that the field should take. This must evaluate to a type that is
                compatible with the field being set.
        """
        if not field.is_array:
            if type(value) is list:
                raise TealInputError(
                    "inner transaction set field {} does not support array value".format(
                        field
                    )
                )
            return InnerTxnFieldExpr(field, cast(Expr, value))
        else:
            if type(value) is not list:
                raise TealInputError(
                    "inner transaction set array field {} with non-array value".format(
                        field
                    )
                )
            for valueIter in value:
                if not isinstance(valueIter, Expr):
                    raise TealInputError(
                        "inner transaction set array field {} with non PyTeal expression array element {}".format(
                            field, valueIter
                        )
                    )
            return Seq(
                *[
                    InnerTxnFieldExpr(field, cast(Expr, valueIter))
                    for valueIter in value
                ]
            )

    @classmethod
    def SetFields(cls, fields: Dict[TxnField, Union[Expr, List[Expr]]]) -> Expr:
        """Set multiple fields of the current inner transaction.

        :any:`InnerTxnBuilder.Begin` must be called before setting any fields on an inner
        transaction.

        Note: For non-array field (e.g., note), setting it twice will overwrite the original value.
              While for array field (e.g., accounts), setting it multiple times will append the values.

        Requires TEAL version 5 or higher. This operation is only permitted in application mode.

        Args:
            fields: A dictionary whose keys are fields to set and whose values are the value each
                field should take. Each value must evaluate to a type that is compatible with the
                field being set.
        """
        fieldsToSet = [cls.SetField(field, value) for field, value in fields.items()]
        return Seq(fieldsToSet)


InnerTxnBuilder.__module__ = "pyteal"

InnerTxn: TxnObject = TxnObject(
    TxnExprBuilder(Op.itxn, "InnerTxn"), TxnaExprBuilder(Op.itxna, None, "InnerTxna")
)

InnerTxn.__module__ = "pyteal"
