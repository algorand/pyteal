from typing import TYPE_CHECKING
from enum import Enum

from ..types import TealType, require_type
from ..ir import TealOp, Op, TealBlock
from .leafexpr import LeafExpr
from .expr import Expr
from .maybe import MaybeValue
from .int import EnumInt
from .global_ import Global

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class OnComplete:
    """An enum of values that :any:`TxnObject.on_completion()` may return."""

    NoOp = EnumInt("NoOp")
    OptIn = EnumInt("OptIn")
    CloseOut = EnumInt("CloseOut")
    ClearState = EnumInt("ClearState")
    UpdateApplication = EnumInt("UpdateApplication")
    DeleteApplication = EnumInt("DeleteApplication")


OnComplete.__module__ = "pyteal"


class AppField(Enum):
    """Enum of app fields used to create :any:`App` objects."""

    optedIn = (Op.app_opted_in, TealType.uint64)
    localGet = (Op.app_local_get, TealType.anytype)
    localGetEx = (Op.app_local_get_ex, TealType.none)
    globalGet = (Op.app_global_get, TealType.anytype)
    globalGetEx = (Op.app_global_get_ex, TealType.none)
    localPut = (Op.app_local_put, TealType.none)
    globalPut = (Op.app_global_put, TealType.none)
    localDel = (Op.app_local_del, TealType.none)
    globalDel = (Op.app_global_del, TealType.none)

    def __init__(self, op: Op, type: TealType) -> None:
        self.op = op
        self.ret_type = type

    def get_op(self) -> Op:
        return self.op

    def type_of(self) -> TealType:
        return self.ret_type


AppField.__module__ = "pyteal"


class App(LeafExpr):
    """An expression related to applications."""

    def __init__(self, field: AppField, args) -> None:
        super().__init__()
        self.field = field
        self.args = args

    def __str__(self):
        ret_str = "({}".format(self.field.get_op())
        for a in self.args:
            ret_str += " " + a.__str__()
        ret_str += ")"
        return ret_str

    def __teal__(self, options: "CompileOptions"):
        return TealBlock.FromOp(options, TealOp(self, self.field.get_op()), *self.args)

    def type_of(self):
        return self.field.type_of()

    @classmethod
    def id(cls) -> Global:
        """Get the ID of the current running application.

        This is the same as :any:`Global.current_application_id()`.
        """
        return Global.current_application_id()

    @classmethod
    def optedIn(cls, account: Expr, app: Expr) -> "App":
        """Check if an account has opted in for an application.

        Args:
            account: An index into Txn.Accounts that corresponds to the account to check,
                must be evaluated to uint64 (or, since v4, an account address that appears in
                Txn.Accounts or is Txn.Sender, must be evaluated to bytes).
            app: An index into Txn.ForeignApps that corresponds to the application to read from,
                must be evaluated to uint64 (or, since v4, an application id that appears in
                Txn.ForeignApps or is the CurrentApplicationID, must be evaluated to int).
        """
        require_type(account, TealType.anytype)
        require_type(app, TealType.uint64)
        return cls(AppField.optedIn, [account, app])

    @classmethod
    def localGet(cls, account: Expr, key: Expr) -> "App":
        """Read from an account's local state for the current application.

        Args:
            account: An index into Txn.Accounts that corresponds to the account to check,
                must be evaluated to uint64 (or, since v4, an account address that appears in
                Txn.Accounts or is Txn.Sender, must be evaluated to bytes).
            key: The key to read from the account's local state. Must evaluate to bytes.
        """
        require_type(account, TealType.anytype)
        require_type(key, TealType.bytes)
        return cls(AppField.localGet, [account, key])

    @classmethod
    def localGetEx(cls, account: Expr, app: Expr, key: Expr) -> MaybeValue:
        """Read from an account's local state for an application.

        Args:
            account: An index into Txn.Accounts that corresponds to the account to check,
                must be evaluated to uint64 (or, since v4, an account address that appears in
                Txn.Accounts or is Txn.Sender, must be evaluated to bytes).
            app: An index into Txn.ForeignApps that corresponds to the application to read from,
                must be evaluated to uint64 (or, since v4, an application id that appears in
                Txn.ForeignApps or is the CurrentApplicationID, must be evaluated to int).
            key: The key to read from the account's local state. Must evaluate to bytes.
        """
        require_type(account, TealType.anytype)
        require_type(app, TealType.uint64)
        require_type(key, TealType.bytes)
        return MaybeValue(
            AppField.localGetEx.get_op(), TealType.anytype, args=[account, app, key]
        )

    @classmethod
    def globalGet(cls, key: Expr) -> "App":
        """Read from the global state of the current application.

        Args:
            key: The key to read from the global application state. Must evaluate to bytes.
        """
        require_type(key, TealType.bytes)
        return cls(AppField.globalGet, [key])

    @classmethod
    def globalGetEx(cls, app: Expr, key: Expr) -> MaybeValue:
        """Read from the global state of an application.

        Args:
            app: An index into Txn.ForeignApps that corresponds to the application to read from,
                must be evaluated to uint64 (or, since v4, an application id that appears in
                Txn.ForeignApps or is the CurrentApplicationID, must be evaluated to uint64).
            key: The key to read from the global application state. Must evaluate to bytes.
        """
        require_type(app, TealType.uint64)
        require_type(key, TealType.bytes)
        return MaybeValue(
            AppField.globalGetEx.get_op(), TealType.anytype, args=[app, key]
        )

    @classmethod
    def localPut(cls, account: Expr, key: Expr, value: Expr) -> "App":
        """Write to an account's local state for the current application.

        Args:
            account: An index into Txn.Accounts that corresponds to the account to check,
                must be evaluated to uint64 (or, since v4, an account address that appears in
                Txn.Accounts or is Txn.Sender, must be evaluated to bytes).
            key: The key to write in the account's local state. Must evaluate to bytes.
            value: The value to write in the account's local state. Can evaluate to any type.
        """
        require_type(account, TealType.anytype)
        require_type(key, TealType.bytes)
        require_type(value, TealType.anytype)
        return cls(AppField.localPut, [account, key, value])

    @classmethod
    def globalPut(cls, key: Expr, value: Expr) -> "App":
        """Write to the global state of the current application.

        Args:
            key: The key to write in the global application state. Must evaluate to bytes.
            value: THe value to write in the global application state. Can evaluate to any type.
        """
        require_type(key, TealType.bytes)
        require_type(value, TealType.anytype)
        return cls(AppField.globalPut, [key, value])

    @classmethod
    def localDel(cls, account: Expr, key: Expr) -> "App":
        """Delete a key from an account's local state for the current application.

        Args:
            account: An index into Txn.Accounts that corresponds to the account to check,
                must be evaluated to uint64 (or, since v4, an account address that appears in
                Txn.Accounts or is Txn.Sender, must be evaluated to bytes).
            key: The key to delete from the account's local state. Must evaluate to bytes.
        """
        require_type(account, TealType.anytype)
        require_type(key, TealType.bytes)
        return cls(AppField.localDel, [account, key])

    @classmethod
    def globalDel(cls, key: Expr) -> "App":
        """Delete a key from the global state of the current application.

        Args:
            key: The key to delete from the global application state. Must evaluate to bytes.
        """
        require_type(key, TealType.bytes)
        return cls(AppField.globalDel, [key])


App.__module__ = "pyteal"


class AppParam:
    @classmethod
    def approvalProgram(cls, app: Expr) -> MaybeValue:
        """Get the bytecode of Approval Program for the application.

        Args:
            app: An index into Txn.ForeignApps that correspond to the application to check.
                Must evaluate to uint64.
        """
        require_type(app, TealType.uint64)
        return MaybeValue(
            Op.app_params_get,
            TealType.bytes,
            immediate_args=["AppApprovalProgram"],
            args=[app],
        )

    @classmethod
    def clearStateProgram(cls, app: Expr) -> MaybeValue:
        """Get the bytecode of Clear State Program for the application.

        Args:
            app: An index into Txn.ForeignApps that correspond to the application to check.
                Must evaluate to uint64.
        """
        require_type(app, TealType.uint64)
        return MaybeValue(
            Op.app_params_get,
            TealType.bytes,
            immediate_args=["AppClearStateProgram"],
            args=[app],
        )

    @classmethod
    def globalNumUnit(cls, app: Expr) -> MaybeValue:
        """Get the number of uint64 values allowed in Global State for the application.

        Args:
            app: An index into Txn.ForeignApps that correspond to the application to check.
                Must evaluate to uint64.
        """
        require_type(app, TealType.uint64)
        return MaybeValue(
            Op.app_params_get,
            TealType.uint64,
            immediate_args=["AppGlobalNumUnit"],
            args=[app],
        )

    @classmethod
    def globalNumByteSlice(cls, app: Expr) -> MaybeValue:
        """Get the number of byte array values allowed in Global State for the application.

        Args:
            app: An index into Txn.ForeignApps that correspond to the application to check.
                Must evaluate to uint64.
        """
        require_type(app, TealType.uint64)
        return MaybeValue(
            Op.app_params_get,
            TealType.uint64,
            immediate_args=["AppGlobalNumByteSlice"],
            args=[app],
        )

    @classmethod
    def localNumUnit(cls, app: Expr) -> MaybeValue:
        """Get the number of uint64 values allowed in Local State for the application.

        Args:
            app: An index into Txn.ForeignApps that correspond to the application to check.
                Must evaluate to uint64.
        """
        require_type(app, TealType.uint64)
        return MaybeValue(
            Op.app_params_get,
            TealType.uint64,
            immediate_args=["AppLocalNumUnit"],
            args=[app],
        )

    @classmethod
    def localNumByteSlice(cls, app: Expr) -> MaybeValue:
        """Get the number of byte array values allowed in Local State for the application.

        Args:
            app: An index into Txn.ForeignApps that correspond to the application to check.
                Must evaluate to uint64.
        """
        require_type(app, TealType.uint64)
        return MaybeValue(
            Op.app_params_get,
            TealType.uint64,
            immediate_args=["AppLocalNumByteSlice"],
            args=[app],
        )

    @classmethod
    def extraProgramPages(cls, app: Expr) -> MaybeValue:
        """Get the number of Extra Program Pages of code space for the application.

        Args:
            app: An index into Txn.ForeignApps that correspond to the application to check.
                Must evaluate to uint64.
        """
        require_type(app, TealType.uint64)
        return MaybeValue(
            Op.app_params_get,
            TealType.uint64,
            immediate_args=["AppExtraProgramPages"],
            args=[app],
        )

    @classmethod
    def creator(cls, app: Expr) -> MaybeValue:
        """Get the creator address for the application.

        Args:
            app: An index into Txn.ForeignApps that correspond to the application to check.
                Must evaluate to uint64.
        """
        require_type(app, TealType.uint64)
        return MaybeValue(
            Op.app_params_get, TealType.bytes, immediate_args=["AppCreator"], args=[app]
        )

    @classmethod
    def address(cls, app: Expr) -> MaybeValue:
        """Get the escrow address for the application.

        Args:
            app: An index into Txn.ForeignApps that correspond to the application to check.
                Must evaluate to uint64.
        """
        require_type(app, TealType.uint64)
        return MaybeValue(
            Op.app_params_get, TealType.bytes, immediate_args=["AppAddress"], args=[app]
        )


AppParam.__module__ = "pyteal"
