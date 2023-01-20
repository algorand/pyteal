from enum import Enum
from typing import Final, TYPE_CHECKING
from pyteal.errors import verifyFieldVersion, verifyProgramVersion

from pyteal.types import TealType, require_type
from pyteal.ir import Op
from pyteal.ast.expr import Expr
from pyteal.ast.maybe import MaybeValue

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class AccountParamField(Enum):
    # fmt: off
    #                    id  |         name               |     type    |  min version
    balance               = (0,  "AcctBalance",            TealType.uint64, 6)  # noqa: E221
    min_balance           = (1,  "AcctMinBalance",         TealType.uint64, 6)  # noqa: E221
    auth_addr             = (2,  "AcctAuthAddr",           TealType.bytes,  6)  # noqa: E221
    total_num_uint        = (3,  "AcctTotalNumUint",       TealType.uint64, 8)  # noqa: E221
    total_num_byte_slice  = (4,  "AcctTotalNumByteSlice",  TealType.uint64, 8)  # noqa: E221
    total_extra_app_pages = (5,  "AcctTotalExtraAppPages", TealType.uint64, 8)  # noqa: E221
    total_apps_created    = (6,  "AcctTotalAppsCreated",   TealType.uint64, 8)  # noqa: E221
    total_apps_opted_in   = (7,  "AcctTotalAppsOptedIn",   TealType.uint64, 8)  # noqa: E221
    total_assets_created  = (8,  "AcctTotalAssetsCreated", TealType.uint64, 8)  # noqa: E221
    total_assets          = (9,  "AcctTotalAssets",        TealType.uint64, 8)  # noqa: E221
    total_boxes           = (10, "AcctTotalBoxes",         TealType.uint64, 8)  # noqa: E221
    total_box_bytes       = (11, "AcctTotalBoxBytes",      TealType.uint64, 8)  # noqa: E221
    # fmt: on

    def __init__(self, id: int, name: str, type: TealType, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.type = type
        self.min_version = min_version

    def type_of(self) -> TealType:
        return self.type


AccountParamField.__module__ = "pyteal"


class AccountParam:
    @staticmethod
    def __makeAccountParamExpr(field: AccountParamField, acct: Expr) -> MaybeValue:
        require_type(acct, TealType.anytype)

        def field_and_program_version_check(options: "CompileOptions"):
            verifyProgramVersion(
                minVersion=Op.acct_params_get.min_version,
                version=options.version,
                msg=f"{Op.acct_params_get.value} unavailable",
            )
            verifyFieldVersion(field.arg_name, field.min_version, options.version)

        return MaybeValue(
            Op.acct_params_get,
            field.type_of(),
            immediate_args=[field.arg_name],
            args=[acct],
            compile_check=field_and_program_version_check,
        )

    @classmethod
    def balance(cls, acct: Expr) -> MaybeValue:
        """Get the current balance in microalgos an account.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.balance, acct)

    @classmethod
    def minBalance(cls, acct: Expr) -> MaybeValue:
        """Get the minimum balance in microalgos for an account.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.min_balance, acct)

    @classmethod
    def authAddr(cls, acct: Expr) -> MaybeValue:
        """Get the authorizing address for an account. If the account is not rekeyed, the empty addresss is returned.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.auth_addr, acct)

    @classmethod
    def totalNumUint(cls, acct: Expr) -> MaybeValue:
        """Get the total number of uint64 values allocated by the account in Global and Local States.

        Requires program version 8 or higher.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.total_num_uint, acct)

    @classmethod
    def totalNumByteSlice(cls, acct: Expr) -> MaybeValue:
        """Get the total number of byte array values allocated by the account in Global and Local States.

        Requires program version 8 or higher.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.total_num_byte_slice, acct)

    @classmethod
    def totalExtraAppPages(cls, acct: Expr) -> MaybeValue:
        """Get the number of extra app code pages used by the account.

        Requires program version 8 or higher.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.total_extra_app_pages, acct)

    @classmethod
    def totalAppsCreated(cls, acct: Expr) -> MaybeValue:
        """Get the number of existing apps created by the account.

        Requires program version 8 or higher.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.total_apps_created, acct)

    @classmethod
    def totalAppsOptedIn(cls, acct: Expr) -> MaybeValue:
        """Get the number of apps the account is opted into.

        Requires program version 8 or higher.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.total_apps_opted_in, acct)

    @classmethod
    def totalAssetsCreated(cls, acct: Expr) -> MaybeValue:
        """Get the number of existing ASAs created by the account.

        Requires program version 8 or higher.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.total_assets_created, acct)

    @classmethod
    def totalAssets(cls, acct: Expr) -> MaybeValue:
        """Get the number of ASAs held by the account (including ASAs the account created).

        Requires program version 8 or higher.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.total_assets, acct)

    @classmethod
    def totalBoxes(cls, acct: Expr) -> MaybeValue:
        """Get the number of existing boxes created by the account's app.

        Requires program version 8 or higher.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.total_boxes, acct)

    @classmethod
    def totalBoxBytes(cls, acct: Expr) -> MaybeValue:
        """Get the total number of bytes used by the account's app's box keys and values.

        Requires program version 8 or higher.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeAccountParamExpr(AccountParamField.total_box_bytes, acct)


AccountParam.__module__ = "pyteal"


class AccountParamObject:
    """Represents information about an account"""

    def __init__(self, account: Expr) -> None:
        """Create a new AccountParamObject for the given account.

        Args:
            account: An index into Txn.accounts that corresponds to the application to check or an
                address available at runtime. May evaluate to uint64 or bytes, respectively.
        """
        self._account: Final = account

    def balance(self) -> MaybeValue:
        """Get the current balance in microAlgos for the account"""
        return AccountParam.balance(self._account)

    def min_balance(self) -> MaybeValue:
        """Get the minimum balance in microAlgos for the account."""
        return AccountParam.minBalance(self._account)

    def auth_address(self) -> MaybeValue:
        """Get the authorizing address for the account.

        If the account is not rekeyed, the empty address is returned."""
        return AccountParam.authAddr(self._account)

    def total_num_uint(self) -> MaybeValue:
        """Get the total number of uint64 values allocated by the account in Global and Local States."""
        return AccountParam.totalNumUint(self._account)

    def total_num_byte_slice(self) -> MaybeValue:
        """Get the total number of byte array values allocated by the account in Global and Local States."""
        return AccountParam.totalNumByteSlice(self._account)

    def total_extra_app_pages(self) -> MaybeValue:
        """Get the number of extra app code pages used by the account."""
        return AccountParam.totalExtraAppPages(self._account)

    def total_apps_created(self) -> MaybeValue:
        """Get the number of existing apps created by the account."""
        return AccountParam.totalAppsCreated(self._account)

    def total_apps_opted_in(self) -> MaybeValue:
        """Get the number of apps the account is opted into."""
        return AccountParam.totalAppsOptedIn(self._account)

    def total_assets_created(self) -> MaybeValue:
        """Get the number of existing ASAs created by the account."""
        return AccountParam.totalAssetsCreated(self._account)

    def total_assets(self) -> MaybeValue:
        """Get the number of ASAs held by the account (including ASAs the account created)."""
        return AccountParam.totalAssets(self._account)

    def total_boxes(self) -> MaybeValue:
        """Get the number of existing boxes created by the account's app."""
        return AccountParam.totalBoxes(self._account)

    def total_box_bytes(self) -> MaybeValue:
        """Get the total number of bytes used by the account's app's box keys and values."""
        return AccountParam.totalBoxBytes(self._account)


AccountParamObject.__module__ = "pyteal"
