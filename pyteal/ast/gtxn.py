from ..types import TealType, require_type
from ..errors import TealInputError
from ..config import MAX_GROUP_SIZE
from .leafexpr import LeafExpr
from .txn import TxnField, str_of_field, type_of_field

class Gtxn(LeafExpr):
    """An expression that accesses a transaction field from a transaction in the current group."""

    def __init__(self, index:int, field:TxnField) -> None:
        require_type(type(index), int)
        if index < 0 or index >= MAX_GROUP_SIZE :
            raise TealInputError("invalid Gtxn index {}, shoud [0, {})".format(
                 index, MAX_GROUP_SIZE))
        self.index = index
        self.field = field

    def __str__(self):
        return "(Gtxn {} {})".format(self.index, str_of_field[self.field])

    def __teal__(self):
        return [["gtxn", str(self.index), str_of_field[self.field]]]
   
    # a series of class methods for better programmer experience
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
   
    def type_of(self):
        return type_of_field[self.field]