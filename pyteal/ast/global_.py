from enum import Enum

from ..types import TealType
from ..ir import TealOp, Op
from .leafexpr import LeafExpr

class GlobalField(Enum):
    min_txn_fee = (0, "MinTxnFee", TealType.uint64)
    min_balance = (1, "MinBalance", TealType.uint64)
    max_txn_life = (2, "MaxTxnLife", TealType.uint64)
    zero_address = (3, "ZeroAddress", TealType.bytes)
    group_size = (4, "GroupSize", TealType.uint64)
    logic_sig_version = (5, "LogicSigVersion", TealType.uint64)
    round = (6, "Round", TealType.uint64)
    latest_timestamp = (7, "LatestTimestamp", TealType.uint64)
    current_app_id = (8, "CurrentApplicationID", TealType.uint64)

    def __init__(self, id: int, name: str, type: TealType) -> None:
        self.id = id
        self.arg_name = name
        self.ret_type = type
    
    def type_of(self) -> TealType:
        return self.ret_type

GlobalField.__module__ = "pyteal"

class Global(LeafExpr):
    """An expression that accesses a global property."""

    def __init__(self, field: GlobalField) -> None:
        self.field = field

    def __teal__(self):
        return [TealOp(Op.global_, self.field.arg_name)]
         
    def __str__(self):
        return "(Global {})".format(self.field.arg_name)
    
    def type_of(self):
        return self.field.type_of()

    @classmethod
    def min_txn_fee(cls) -> 'Global':
        """Get the minumum transaction fee in micro Algos."""
        return cls(GlobalField.min_txn_fee)

    @classmethod
    def min_balance(cls) -> 'Global':
        """Get the minumum balance in micro Algos."""
        return cls(GlobalField.min_balance)

    @classmethod
    def max_txn_life(cls) -> 'Global':
        """Get the maximum number of rounds a transaction can have."""
        return cls(GlobalField.max_txn_life)

    @classmethod
    def zero_address(cls) -> 'Global':
        """Get the 32 byte zero address."""
        return cls(GlobalField.zero_address)

    @classmethod
    def group_size(cls) -> 'Global':
        """Get the number of transactions in this atomic transaction group.
        
        This will be at least 1.
        """
        return cls(GlobalField.group_size)

    @classmethod
    def logic_sig_version(cls) -> 'Global':
        """Get the maximum supported TEAL version."""
        return cls(GlobalField.logic_sig_version)
    
    @classmethod
    def round(cls) -> 'Global':
        """Get the current round number."""
        return cls(GlobalField.round)
    
    @classmethod
    def latest_timestamp(cls) -> 'Global':
        """Get the latest confirmed block UNIX timestamp.
        
        Fails if negative."""
        return cls(GlobalField.latest_timestamp)
    
    @classmethod
    def current_application_id(cls) -> 'Global':
        """Get the ID of the current application executing.
        
        Fails if no application is executing."""
        return cls(GlobalField.current_app_id)

Global.__module__ = "pyteal"
