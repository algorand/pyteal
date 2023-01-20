from typing import TYPE_CHECKING
from enum import Enum

from pyteal.types import TealType
from pyteal.errors import verifyFieldVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.leafexpr import LeafExpr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class GlobalField(Enum):
    min_txn_fee = (0, "MinTxnFee", TealType.uint64, 2)
    min_balance = (1, "MinBalance", TealType.uint64, 2)
    max_txn_life = (2, "MaxTxnLife", TealType.uint64, 2)
    zero_address = (3, "ZeroAddress", TealType.bytes, 2)
    group_size = (4, "GroupSize", TealType.uint64, 2)
    logic_sig_version = (5, "LogicSigVersion", TealType.uint64, 2)
    round = (6, "Round", TealType.uint64, 2)
    latest_timestamp = (7, "LatestTimestamp", TealType.uint64, 2)
    current_app_id = (8, "CurrentApplicationID", TealType.uint64, 2)
    creator_address = (9, "CreatorAddress", TealType.bytes, 3)
    current_app_address = (10, "CurrentApplicationAddress", TealType.bytes, 5)
    group_id = (11, "GroupID", TealType.bytes, 5)
    opcode_budget = (12, "OpcodeBudget", TealType.uint64, 6)
    caller_app_id = (13, "CallerApplicationID", TealType.uint64, 6)
    caller_app_address = (14, "CallerApplicationAddress", TealType.bytes, 6)

    def __init__(self, id: int, name: str, type: TealType, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.ret_type = type
        self.min_version = min_version

    def type_of(self) -> TealType:
        return self.ret_type


GlobalField.__module__ = "pyteal"


class Global(LeafExpr):
    """An expression that accesses a global property."""

    def __init__(self, field: GlobalField) -> None:
        super().__init__()
        self.field = field

    def __teal__(self, options: "CompileOptions"):
        verifyFieldVersion(self.field.arg_name, self.field.min_version, options.version)

        op = TealOp(self, Op.global_, self.field.arg_name)
        return TealBlock.FromOp(options, op)

    def __str__(self):
        return "(Global {})".format(self.field.arg_name)

    def type_of(self):
        return self.field.type_of()

    @classmethod
    def min_txn_fee(cls) -> "Global":
        """Get the minimum transaction fee in micro Algos."""
        return cls(GlobalField.min_txn_fee)

    @classmethod
    def min_balance(cls) -> "Global":
        """Get the minimum balance in micro Algos."""
        return cls(GlobalField.min_balance)

    @classmethod
    def max_txn_life(cls) -> "Global":
        """Get the maximum number of rounds a transaction can have."""
        return cls(GlobalField.max_txn_life)

    @classmethod
    def zero_address(cls) -> "Global":
        """Get the 32 byte zero address."""
        return cls(GlobalField.zero_address)

    @classmethod
    def group_size(cls) -> "Global":
        """Get the number of transactions in this atomic transaction group.

        This will be at least 1.
        """
        return cls(GlobalField.group_size)

    @classmethod
    def logic_sig_version(cls) -> "Global":
        """Get the maximum supported program version."""
        return cls(GlobalField.logic_sig_version)

    @classmethod
    def round(cls) -> "Global":
        """Get the current round number."""
        return cls(GlobalField.round)

    @classmethod
    def latest_timestamp(cls) -> "Global":
        """Get the latest confirmed block UNIX timestamp.

        Fails if negative."""
        return cls(GlobalField.latest_timestamp)

    @classmethod
    def current_application_id(cls) -> "Global":
        """Get the ID of the current application executing.

        Fails during Signature mode."""
        return cls(GlobalField.current_app_id)

    @classmethod
    def creator_address(cls) -> "Global":
        """Address of the creator of the current application.

        Fails during Signature mode. Requires program version 3 or higher."""
        return cls(GlobalField.creator_address)

    @classmethod
    def current_application_address(cls) -> "Global":
        """Get the address of that the current application controls.

        Fails during Signature mode. Requires program version 5 or higher."""
        return cls(GlobalField.current_app_address)

    @classmethod
    def group_id(cls) -> "Global":
        """Get the ID of the current transaction group.

        If the current transaction is not part of a group, this will return 32 zero bytes.

        Requires program version 5 or higher."""
        return cls(GlobalField.group_id)

    @classmethod
    def opcode_budget(cls) -> "Global":
        """Get the remaining opcode execution budget

        Requires program version 6 or higher."""
        return cls(GlobalField.opcode_budget)

    @classmethod
    def caller_app_id(cls) -> "Global":
        """Get the id of the app that submitted the InnerTransaction that triggered this app to execute.

        If not called from another app, this will return 0

        Requires program version 6 or higher."""
        return cls(GlobalField.caller_app_id)

    @classmethod
    def caller_app_address(cls) -> "Global":
        """Get the address of the app that submitted the InnerTransaction that triggered this app to execute.

        If not called from another app, this will return the ZeroAddress

        Requires program version 6 or higher."""
        return cls(GlobalField.caller_app_address)


Global.__module__ = "pyteal"
