from ..types import TealType, require_type
from ..ir import TealOp, Op
from ..errors import TealInputError, TealTypeError
from ..config import MAX_GROUP_SIZE
from .leafexpr import LeafExpr
from .txn import TxnField

class Gtxna(LeafExpr):
    """An expression that accesses a transaction array field from a transaction in the current group."""

    def __init__(self, txIndex: int, field: TxnField, index: int) -> None:
        if type(index) != int:
            raise TealTypeError(type(index), int)
        if index < 0 or index >= MAX_GROUP_SIZE:
            raise TealInputError("invalid Gtxn index {}, shoud [0, {})".format(index, MAX_GROUP_SIZE))
        self.txIndex = txIndex
        self.field = field
        self.index = index
    
    def __str__(self):
        return "(Gxna {} {} {})".format(self.txIndex, self.field.arg_name, self.index)
    
    def __teal__(self):
        return [TealOp(Op.gtxna, self.txIndex, self.field.arg_name, self.index)]
    
    def type_of(self):
        return self.field.type_of()

class Gtxn(LeafExpr):
    """An expression that accesses a transaction field from a transaction in the current group."""

    def __init__(self, index:int, field:TxnField) -> None:
        if type(index) != int:
            raise TealTypeError(type(index), int)
        if index < 0 or index >= MAX_GROUP_SIZE:
            raise TealInputError("invalid Gtxn index {}, shoud [0, {})".format(index, MAX_GROUP_SIZE))
        self.index = index
        self.field = field

    def __str__(self):
        return "(Gtxn {} {})".format(self.index, self.field.arg_name)

    def __teal__(self):
        return [TealOp(Op.gtxn, self.index, self.field.arg_name)]
    
    def type_of(self):
        return self.field.type_of()

    @classmethod
    def sender(cls, index):
        return cls(index, TxnField.sender)
   
    @classmethod
    def fee(cls, index):
        return cls(index, TxnField.fee)

    @classmethod
    def first_valid(cls, index):
        return cls(index, TxnField.first_valid)

    @classmethod
    def lease(cls, index):
        return cls(index, TxnField.lease)
   
    @classmethod
    def last_valid(cls, index):
        return cls(index, TxnField.last_valid)

    @classmethod
    def note(cls, index):
        return cls(index, TxnField.note)

    @classmethod
    def receiver(cls, index):
        return cls(index, TxnField.receiver)

    @classmethod
    def amount(cls, index):
        return cls(index, TxnField.amount)

    @classmethod
    def close_remainder_to(cls, index):
        return cls(index, TxnField.close_remainder_to)

    @classmethod
    def vote_pk(cls, index):
        return cls(index, TxnField.vote_pk)

    @classmethod
    def selection_pk(cls, index):
        return cls(index, TxnField.selection_pk)

    @classmethod
    def vote_first(cls, index):
        return cls(index, TxnField.vote_first)

    @classmethod
    def vote_last(cls, index):
        return cls(index, TxnField.vote_last)

    @classmethod
    def vote_key_dilution(cls, index):
        return cls(index, TxnField.vote_key_dilution)

    @classmethod
    def type(cls, index):
        return cls(index, TxnField.type)

    @classmethod
    def type_enum(cls, index):
        return cls(index, TxnField.type_enum)

    @classmethod
    def xfer_asset(cls, index):
        return cls(index, TxnField.xfer_asset)

    @classmethod
    def asset_amount(cls, index):
        return cls(index, TxnField.asset_amount)

    @classmethod
    def asset_sender(cls, index):
        return cls(index, TxnField.asset_sender)

    @classmethod
    def asset_receiver(cls, index):
        return cls(index, TxnField.asset_receiver)

    @classmethod
    def asset_close_to(cls, index):
        return cls(index, TxnField.asset_close_to)

    @classmethod
    def group_index(cls, index):
        return cls(index, TxnField.group_index)

    @classmethod
    def tx_id(cls, index):
        return cls(index, TxnField.tx_id)

    @classmethod
    def application_id(cls, index):
        return cls(index, TxnField.application_id)

    @classmethod
    def on_completion(cls, index):
        return cls(index, TxnField.on_completion)

    @classmethod
    def approval_program(cls, index):
        return cls(index, TxnField.approval_program)
    
    @classmethod
    def clear_state_program(cls, index):
        return cls(index, TxnField.clear_state_program)
    
    @classmethod
    def rekey_to(cls, index):
        return cls(index, TxnField.rekey_to)
    
    @classmethod
    def config_asset(cls, index):
        return cls(index, TxnField.config_asset)
    
    @classmethod
    def config_asset_total(cls, index):
        return cls(index, TxnField.config_asset_total)

    @classmethod
    def config_asset_decimals(cls, index):
        return cls(index, TxnField.config_asset_decimals)
    
    @classmethod
    def config_asset_default_frozen(cls, index):
        return cls(index, TxnField.config_asset_default_frozen)
    
    @classmethod
    def config_asset_unit_name(cls, index):
        return cls(index, TxnField.config_asset_unit_name)

    @classmethod
    def config_asset_name(cls, index):
        return cls(index, TxnField.config_asset_name)
    
    @classmethod
    def config_asset_url(cls, index):
        return cls(index, TxnField.config_asset_url)
    
    @classmethod
    def config_asset_metadata_hash(cls, index):
        return cls(index, TxnField.config_asset_metadata_hash)
    
    @classmethod
    def config_asset_manager(cls, index):
        return cls(index, TxnField.config_asset_manager)
    
    @classmethod
    def config_asset_reserve(cls, index):
        return cls(index, TxnField.config_asset_reserve)
    
    @classmethod
    def config_asset_freeze(cls, index):
        return cls(index, TxnField.config_asset_freeze)
    
    @classmethod
    def config_asset_clawback(cls, index):
        return cls(index, TxnField.config_asset_clawback)
    
    @classmethod
    def freeze_asset(cls, index):
        return cls(index, TxnField.freeze_asset)
    
    @classmethod
    def freeze_asset_account(cls, index):
        return cls(index, TxnField.freeze_asset_account)
    
    @classmethod
    def freeze_asset_frozen(cls, index):
        return cls(index, TxnField.freeze_asset_frozen)
    
    class ArrayAccessor:

        def __init__(self, txIndex: int, accessField: TxnField, lengthField: TxnField) -> None:
            self.txIndex = txIndex
            self.accessField = accessField
            self.lengthField = lengthField
        
        def length(self):
            """Get the length of this array."""
            return Gtxn(self.txIndex, self.lengthField)
        
        def __getitem__(self, index: int):
            """Get the value at an index in this array.
            
            Args:
                index: Must not be negative.
            """
            if not isinstance(index, int) or index < 0:
                raise TealInputError("Invalid array index: {}".format(index))

            return Gtxna(self.txIndex, self.accessField, index)

    @classmethod
    def application_args(cls, index: int):
        return cls.ArrayAccessor(index, TxnField.application_args, TxnField.num_app_args)

    @classmethod
    def accounts(cls, index: int):
        return cls.ArrayAccessor(index, TxnField.accounts, TxnField.num_accounts)
