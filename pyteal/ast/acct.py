from typing import TYPE_CHECKING

from ..types import TealType, require_type
from ..ir import Op
from .expr import Expr
from .maybe import MaybeValue

if TYPE_CHECKING:
    from ..compiler import CompileOptions


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
