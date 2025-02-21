from enum import Enum
from typing import Final, TYPE_CHECKING
from pyteal.errors import verifyFieldVersion, verifyProgramVersion

from pyteal.types import TealType, require_type
from pyteal.ir import Op
from pyteal.ast.expr import Expr
from pyteal.ast.maybe import MaybeValue

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class VoterParamField(Enum):
    # fmt: off
    #                    id  |         name               |     type    |  min version
    balance               = (0,  "VoterBalance",            TealType.uint64, 11)  # noqa: E221
    incentive_eligible    = (1,  "VoterIncentiveEligible",  TealType.uint64, 11)  # noqa: E221
    # fmt: on

    def __init__(self, id: int, name: str, type: TealType, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.type = type
        self.min_version = min_version

    def type_of(self) -> TealType:
        return self.type


VoterParamField.__module__ = "pyteal"


class VoterParam:
    @staticmethod
    def __makeVoterParamExpr(field: VoterParamField, acct: Expr) -> MaybeValue:
        require_type(acct, TealType.anytype)

        def field_and_program_version_check(options: "CompileOptions"):
            verifyProgramVersion(
                minVersion=Op.voter_params_get.min_version,
                version=options.version,
                msg=f"{Op.voter_params_get.value} unavailable",
            )
            verifyFieldVersion(field.arg_name, field.min_version, options.version)

        return MaybeValue(
            Op.voter_params_get,
            field.type_of(),
            immediate_args=[field.arg_name],
            args=[acct],
            compile_check=field_and_program_version_check,
        )

    @classmethod
    def balance(cls, acct: Expr) -> MaybeValue:
        """Get the balance in microalgos for an account in the balance round (current - 320).

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeVoterParamExpr(VoterParamField.balance, acct)

    @classmethod
    def incentiveEligible(cls, acct: Expr) -> MaybeValue:
        """Get account's eligibility status for block incentives as of the balance round.

        Requires program version 11 or higher.

        Args:
            acct: An index into Txn.accounts that corresponds to the application to check or an address available at runtime.
                May evaluate to uint64 or an address.
        """
        return cls.__makeVoterParamExpr(VoterParamField.incentive_eligible, acct)


VoterParam.__module__ = "pyteal"


class VoterParamObject:
    """Represents information about an account"""

    def __init__(self, account: Expr) -> None:
        """Create a new VoterParamObject for the given account.

        Args:
            account: An index into Txn.accounts that corresponds to the application to check or an
                address available at runtime. May evaluate to uint64 or bytes, respectively.
        """
        self._account: Final = account

    def balance(self) -> MaybeValue:
        """Get the current balance in microAlgos for the account"""
        return VoterParam.balance(self._account)

    def incentive_eligible(self) -> MaybeValue:
        """Get account's eligibility status for block incentives."""
        return VoterParam.incentiveEligible(self._account)


VoterParamObject.__module__ = "pyteal"
