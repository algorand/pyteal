from enum import Enum

from ..types import TealType
from .leafexpr import LeafExpr

class TxnField(Enum):
     sender = 0
     fee = 1
     first_valid = 2
     last_valid = 3
     note = 4
     lease = 5
     receiver = 6
     amount = 7
     close_remainder_to = 8
     vote_pk = 9
     selection_pk = 10
     vote_first =11
     vote_last = 12
     vote_key_dilution = 13
     type = 14
     type_enum = 15
     xfer_asset = 16
     asset_amount = 17
     asset_sender = 18
     asset_receiver = 19
     asset_close_to = 20
     group_index = 21
     tx_id = 22

# data types of txn fields
type_of_field = {
     TxnField.sender: TealType.bytes,
     TxnField.fee: TealType.uint64,
     TxnField.first_valid: TealType.uint64,
     TxnField.last_valid: TealType.uint64,
     TxnField.note: TealType.bytes,
     TxnField.lease: TealType.bytes,
     TxnField.receiver: TealType.bytes,
     TxnField.amount: TealType.uint64,
     TxnField.close_remainder_to: TealType.bytes,
     TxnField.vote_pk: TealType.bytes,
     TxnField.selection_pk: TealType.bytes,
     TxnField.vote_first: TealType.uint64,
     TxnField.vote_last: TealType.uint64,
     TxnField.vote_key_dilution: TealType.uint64,
     TxnField.type: TealType.bytes,
     TxnField.type_enum: TealType.uint64,
     TxnField.xfer_asset: TealType.uint64,
     TxnField.asset_amount: TealType.uint64,
     TxnField.asset_sender: TealType.bytes,
     TxnField.asset_receiver: TealType.bytes,
     TxnField.asset_close_to: TealType.bytes,
     TxnField.group_index: TealType.uint64,
     TxnField.tx_id: TealType.bytes
}

str_of_field = {
     TxnField.sender: "Sender",
     TxnField.fee: "Fee",
     TxnField.first_valid: "FirstValid",
     TxnField.last_valid: "LastValid",
     TxnField.note: "Note",
     TxnField.lease: "Lease",
     TxnField.receiver: "Receiver",
     TxnField.amount: "Amount",
     TxnField.close_remainder_to: "CloseRemainderTo",
     TxnField.vote_pk: "VotePK",
     TxnField.selection_pk: "SelectionPK",
     TxnField.vote_first: "VoteFirst",
     TxnField.vote_last: "VoteLast",
     TxnField.vote_key_dilution: "VoteKeyDilution",
     TxnField.type: "Type",
     TxnField.type_enum: "TypeEnum",
     TxnField.xfer_asset: "XferAsset",
     TxnField.asset_amount: "AssetAmount",
     TxnField.asset_sender: "AssetSender",
     TxnField.asset_receiver: "AssetReceiver",
     TxnField.asset_close_to: "AssetCloseTo",
     TxnField.group_index: "GroupIndex",
     TxnField.tx_id: "TxID"
}

# get a field from the current txn
class Txn(LeafExpr):

    # default constructor
    def __init__(self, field:TxnField) -> None:
        self.field = field

    def __str__(self):
        return "(Txn {})".format(str_of_field[self.field])

    def __teal__(self):
        return [["txn", str_of_field[self.field]]]
   
    # a series of class methods for better programmer experience
    @classmethod
    def sender(cls):
        return cls(TxnField.sender)
   
    @classmethod
    def fee(cls):
        return cls(TxnField.fee)

    @classmethod
    def first_valid(cls):
        return cls(TxnField.first_valid)
   
    @classmethod
    def last_valid(cls):
        return cls(TxnField.last_valid)

    @classmethod
    def note(cls):
        return cls(TxnField.note)

    @classmethod
    def lease(cls):
        return cls(TxnField.lease)
   
    @classmethod
    def receiver(cls):
        return cls(TxnField.receiver)

    @classmethod
    def amount(cls):
        return cls(TxnField.amount)

    @classmethod
    def close_remainder_to(cls):
        return cls(TxnField.close_remainder_to)

    @classmethod
    def vote_pk(cls):
        return cls(TxnField.vote_pk)

    @classmethod
    def selection_pk(cls):
        return cls(TxnField.selection_pk)

    @classmethod
    def vote_first(cls):
        return cls(TxnField.vote_first)

    @classmethod
    def vote_last(cls):
        return cls(TxnField.vote_last)

    @classmethod
    def vote_key_dilution(cls):
        return cls(TxnField.vote_key_dilution)

    @classmethod
    def type(cls):
        return cls(TxnField.type)

    @classmethod
    def type_enum(cls):
        return cls(TxnField.type_enum)

    @classmethod
    def xfer_asset(cls):
        return cls(TxnField.xfer_asset)

    @classmethod
    def asset_amount(cls):
        return cls(TxnField.asset_amount)

    @classmethod
    def asset_sender(cls):
        return cls(TxnField.asset_sender)

    @classmethod
    def asset_receiver(cls):
        return cls(TxnField.asset_receiver)

    @classmethod
    def asset_close_to(cls):
        return cls(TxnField.asset_close_to)

    @classmethod
    def group_index(cls):
        return cls(TxnField.group_index)

    @classmethod
    def tx_id(cls):
        return cls(TxnField.tx_id)
   
    def type_of(self):
        return type_of_field[self.field]
