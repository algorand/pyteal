from typing import Final

from pyteal.types import TealType, require_type
from pyteal.ir import Op
from pyteal.ast.expr import Expr
from pyteal.ast.maybe import MaybeValue


class AccountParam:
    @classmethod
    def balance(cls, acct: Expr) -> MaybeValue:
        """Get the current balance in microalgos an account.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        require_type(acct, TealType.anytype)
        return MaybeValue(
            Op.acct_params_get,
            TealType.uint64,
            immediate_args=["AcctBalance"],
            args=[acct],
        )

    @classmethod
    def minBalance(cls, acct: Expr) -> MaybeValue:
        """Get the minimum balance in microalgos for an account.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        require_type(acct, TealType.anytype)
        return MaybeValue(
            Op.acct_params_get,
            TealType.uint64,
            immediate_args=["AcctMinBalance"],
            args=[acct],
        )

    @classmethod
    def authAddr(cls, acct: Expr) -> MaybeValue:
        """Get the authorizing address for an account. If the account is not rekeyed, the empty addresss is returned.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        require_type(acct, TealType.anytype)
        return MaybeValue(
            Op.acct_params_get,
            TealType.bytes,
            immediate_args=["AcctAuthAddr"],
            args=[acct],
        )


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


AccountParamObject.__module__ = "pyteal"
