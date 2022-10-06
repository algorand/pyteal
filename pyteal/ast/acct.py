from enum import Enum
from typing import Final, TYPE_CHECKING
from pyteal.errors import verifyFieldVersion

from pyteal.types import TealType, require_type
from pyteal.ir import Op
from pyteal.ast.leafexpr import LeafExpr
from pyteal.ast.expr import Expr
from pyteal.ast.maybe import MaybeValue

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class AccountParamField(Enum):
    # fmt: off
    #                    id  |         name               |     type    |  min version
    balance               = (0,  "AcctBalance",            TealType.uint64, 6)
    min_balance           = (1,  "AcctMinBalance",         TealType.uint64, 6)
    auth_addr             = (2,  "AcctAuthAddr",           TealType.bytes,  6)
    total_num_uint        = (3,  "AcctTotalNumUint",       TealType.uint64, 8)
    total_num_byte_slice  = (4,  "AcctTotalNumByteSlice",  TealType.uint64, 8)
    total_extra_app_pages = (5,  "AcctTotalExtraAppPages", TealType.uint64, 8)
    total_apps_created    = (6,  "AcctTotalAppsCreated",   TealType.uint64, 8)
    total_apps_opted_in   = (7,  "AcctTotalAppsOptedIn",   TealType.uint64, 8)
    total_box_bytes       = (8,  "AcctTotalBoxBytes",      TealType.uint64, 8)
    total_assets_created  = (9,  "AcctTotalAssetsCreated", TealType.uint64, 8)
    total_assets          = (10, "AcctTotalAssets",        TealType.uint64, 8)
    total_boxes           = (11, "AcctTotalBoxes",         TealType.uint64, 8)
    # fmt: on

    def __init__(self, id: int, name: str, type: TealType, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.type = type
        self.min_version = min_version

    def type_of(self) -> TealType:
        return self.type


AccountParamField.__module__ = "pyteal"


class AccountParamExpr(MaybeValue):
    """A maybe value expression that accesses an account parameter field from a given account."""

    def __init__(self, field: AccountParamField, acct: Expr) -> None:
        super().__init__(
            Op.acct_params_get,
            field.type_of(),
            immediate_args=[field.arg_name],
            args=[acct]
        )
        require_type(acct, TealType.anytype)

        self.field = field
        self.acct = acct

    def __str__(self):
        return "(AccountParam {} {})".format(self.field.arg_name, self.acct)

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(self.field.arg_name, self.field.min_version, options.version)

        return super().__teal__(options)


AccountParamExpr.__module__ = "pyteal"


class AccountParam:
    @classmethod
    def balance(cls, acct: Expr) -> AccountParamExpr:
        """Get the current balance in microalgos an account.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return AccountParamExpr(AccountParamField.balance, acct)

    @classmethod
    def minBalance(cls, acct: Expr) -> AccountParamExpr:
        """Get the minimum balance in microalgos for an account.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return AccountParamExpr(AccountParamField.min_balance, acct)

    @classmethod
    def authAddr(cls, acct: Expr) -> AccountParamExpr:
        """Get the authorizing address for an account. If the account is not rekeyed, the empty addresss is returned.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return AccountParamExpr(AccountParamField.auth_addr, acct)


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

    def balance(self) -> AccountParamExpr:
        """Get the current balance in microAlgos for the account"""
        return AccountParam.balance(self._account)

    def min_balance(self) -> AccountParamExpr:
        """Get the minimum balance in microAlgos for the account."""
        return AccountParam.minBalance(self._account)

    def auth_address(self) -> AccountParamExpr:
        """Get the authorizing address for the account.

        If the account is not rekeyed, the empty address is returned."""
        return AccountParam.authAddr(self._account)


AccountParamObject.__module__ = "pyteal"
