#!/usr/bin/env python3
"""
Operators on uint64

"""

from typing import ClassVar, List
from enum import Enum

from .util import TealType, TealTypeError, TealTypeMismatchError, require_type
from .expr import Expr, BinaryExpr, UnaryExpr, NaryExpr, LeafExpr, TealType


class TxnField(Enum):
     sender = 0
     fee = 1
     first_valid = 2
     last_valid = 3
     note = 4
     receiver = 5
     amount = 6
     close_remainder_to = 7
     vote_pk = 8
     selection_pk = 9
     vote_first =10
     vote_last = 11
     vote_key_dilution = 12
     type = 13
     type_enum = 14
     xfer_asset = 15
     asset_amount = 16
     asset_sender = 17
     asset_receiver = 18
     asset_close_to = 19
     group_index = 20
     tx_id = 21
     sender_balance = 22
     lease = 23     
     

# data types of txn fields
type_of_field = {
     TxnField.sender: TealType.bytes,
     TxnField.fee: TealType.uint64,
     TxnField.first_valid: TealType.uint64,
     TxnField.last_valid: TealType.uint64,
     TxnField.note: TealType.bytes,
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
     TxnField.xfer_asset: TealType.bytes,
     TxnField.asset_amount: TealType.uint64,
     TxnField.asset_sender: TealType.bytes,
     TxnField.asset_receiver: TealType.bytes,
     TxnField.asset_close_to: TealType.bytes,
     TxnField.group_index: TealType.uint64,
     TxnField.tx_id: TealType.bytes,
     TxnField.sender_balance: TealType.uint64,
     TxnField.lease: TealType.bytes
}

str_of_field = {
     TxnField.sender: "Sender",
     TxnField.fee: "Fee",
     TxnField.first_valid: "FirstValid",
     TxnField.last_valid: "LastValid",
     TxnField.note: "Note",
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
     TxnField.tx_id: "TxID",
     TxnField.sender_balance: "SenderBalance",
     TxnField.lease: "Lease"
}

class GlobalField(Enum):
     round = 0,
     min_txn_fee = 1
     min_balance = 2
     max_txn_life = 3
     time_stamp = 4
     zero_address = 5
     group_size = 6


type_of_global_field = {
     GlobalField.round: TealType.uint64,
     GlobalField.min_txn_fee: TealType.uint64,
     GlobalField.min_balance: TealType.uint64,
     GlobalField.max_txn_life: TealType.uint64,
     GlobalField.time_stamp: TealType.uint64,
     GlobalField.zero_address: TealType.bytes,
     GlobalField.group_size: TealType.uint64
}

str_of_global_field = {
     GlobalField.round: "Round",
     GlobalField.min_txn_fee: "MinTxnFee",
     GlobalField.min_balance: "MinBalance",
     GlobalField.max_txn_life: "MaxTxnLife",
     GlobalField.time_stamp: "TimeStamp",
     GlobalField.zero_address: "ZeroAddress",
     GlobalField.group_size: "GroupSize"
}


class Addr(LeafExpr):
    address: ClassVar[str]
    
    # default constructor
    def __init__(self, address:str):        
        #TODO: check the validity of the address
        self.address = address

    def __str__(self):
        return "(address: {})".format(self.address)

    def type_of(self):
        return TealType.raw_bytes


class Byte(LeafExpr):
    base: ClassVar[str]
    byte_str: ClassVar[str]

    #default constructor
    def __init__(self, base:str, byte_str:str):
        if base == "base32":
            self.base = base
        elif base == "base64":
            self.base = base
        else:
            raise "Byte: Invalid base"

    def __str__(self):
        return "({} bytes: {})".format(self.base, self.byte_str)

    def type_of(self):
        return TealType.raw_bytes


class Int(LeafExpr):
    value: ClassVar[int]

    # default contructor
    def __init__(self, value:int):
        if value >= 0 and value < 2 ** 64:
            self.value = value
        else:
            raise "Int: {} is  out of range".format(value)

    def __str__(self):
        return "(Int: {})".format(self.value)

    def type_of(self):
        return TealType.uint64
    
class Arg(LeafExpr):
    index: ClassVar[int]

    # default constructor
    def __init__(self, index:int):
        if index < 0 or index > 255:
            raise "Invalid arg index: {}".format(index)

        self.index = index

    def __str__(self):
        return "(arg {})".format(index)

    def type_of(self):
        return TealType.raw_bytes


class And(BinaryExpr):

    # default constructor
    # TODO: operator override design
    def __init__(self, left:Expr, right:Expr):
        require_type(left.type_of(), TealType.uint64)
        require_type(right.type_of(), TealType.uint64)
        self.left = left
        self.right = right

    def __str__(self):
        return "(and {} {})".format(self.left, self.right)

    def type_of(self):
        return TealType.uint64


class Or(BinaryExpr):

    # default constructor
    def __init__(self, left:Expr, right:Expr):
        require_type(left.type_of(), TealType.uint64)
        require_type(right.type_of(), TealType.uint64)
        self.left = left
        self.right = right

    def __str__(self):
        return "(or {} {})".format(self.left, self.right) 

    def type_of(self):
        return TealType.uint64
    

# less than
class Lt(BinaryExpr):

    # default constructor
    def __init__(self, left:Expr, right:Expr):
        require_type(left.type_of(), TealType.uint64)
        require_type(right.type_of(), TealType.uint64)
        self.left = left
        self.right = right

    def __str__(self):
        return "(< {} {})".format(self.left, self.right)

    def type_of(self):
        return TealType.uint64


# less than
class Gt(BinaryExpr):

    # default constructor
    def __init__(self, left:Expr, right:Expr):
        self.left = left
        self.right = right

    def __str__(self):
        return "(> {} {})".format(self.left, self.right)
        
    def type_of(self):
        return TealType.uint64    


# a polymorphic eq
class Eq(BinaryExpr):

    # default constructor
    def __init__(self, left:Expr, right:Expr):
        # type checking
        t1 = left.type_of()
        t2 = right.type_of()
        if t1 != t2:
            raise TealTypeMismatchError(t1, t2)

        self.left = left
        self.right = right

    def __str__(self):
         return "(== {} {})".format(self.left, self.right)
        
    def type_of(self):
        return TealType.uint64
    
    
# return the length of a bytes value
class Len(UnaryExpr):

    # default constructor
    def __init__(self, child:Expr):
        self.child = child

    def __str__(self):
         return "(len {})".format(self.child)

    def type_of(self):
        return TealType.uint64
    

# get a field from the current txn
class Txn(LeafExpr):
    field: ClassVar[TxnField]

    # default constructor
    def __init__(self, field:TxnField):
        self.field = field

    def __str__(self):
        return "(Txn {})".format(str_of_field[self.field])

    def type_of(self):
        return type_of_field[self.field]
    

class Global(LeafExpr):
    field: ClassVar[GlobalField]

    # default constructor
    def __init__(self, field:GlobalField):
        self.field = field

    def __str__(self):
        return "(Global {})".format(str_of_global_field[self.field])

    def type_of(self):
        return type_of_global_field(self.field)


# ed25519 signature verification
class Ed25519Verify(NaryExpr):

    # default constructor
    def __init__(self, arg0:Expr, arg1:Expr, arg2:Expr):
        require_type(arg0.type_of(), TealType.bytes)
        require_type(arg1.type_of(), TealType.bytes)
        require_type(arg2.type_of(), TealType.bytes)
        
        arg_list = [arg0, arg1, arg2]
        self.args = arg_list

    def __str__(self):
         return "(ed25519verify {})".format(self.child)
        
    def type_of(self):
        return TealType.uint64


