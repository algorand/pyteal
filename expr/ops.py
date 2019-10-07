#!/usr/bin/env python3
"""
Operators on uint64

"""

from core import Expr, BinaryExpr, UnaryExpr, NaryExpr, LeafExpr, TealType
from typing import ClassVar, List
from enum import Enum

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


class Addr(LeafExpr):
    address: ClassVar[str]
    
    # default constructor
    def __init__(self, address:str):        
        #TODO: check the validity of the address
        self.address = address
        
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

    def type_of(self):
        return TealType.uint64
    
class Arg(LeafExpr):
    index: ClassVar[int]

    # default constructor
    def __init__(self, index:int):
        if index < 0 or index > 255:
            raise "Invalid arg index: {}".format(index)

        self.index = index

    def type_of(self):
        return TealType.raw_bytes


class And(BinaryExpr):
    left: ClassVar[Expr]
    right: ClassVar[Expr]

    # default constructor
    # TODO: operator override design
    def __init__(self, left:Expr, right:Expr):
        self.left = left
        self.right = right

    def type_of(self):
        return TealType.uint64


class Or(BinaryExpr):
    left: ClassVar[Expr]
    right: ClassVar[Expr]

    # default constructor
    def __init__(self, left:Expr, right:Expr):
        self.left = left
        self.right = right

    def type_of(self):
        return TealType.uint64
    

# less than
class LT(BinaryExpr):
    left: ClassVar[Expr]
    right: ClassVar[Expr]

    # default constructor
    def __init__(self, left:Expr, right:Expr):
        self.left = left
        self.right = right

    def type_of(self):
        return TealType.uint64


# less than
class GT(BinaryExpr):
    left: ClassVar[Expr]
    right: ClassVar[Expr]

    # default constructor
    def __init__(self, left:Expr, right:Expr):
        self.left = left
        self.right = right

    def type_of(self):
        return TealType.uint64    

    
# return the length of a bytes value
class Len(UnaryExpr):
    child: ClassVar[Expr]

    # default constructor
    def __init__(self, child:Expr):
        self.child = child

    def type_of(self):
        return TealType.uint64
    

# get a field from the current txn
class Txn(LeafExpr):
    field: ClassVar[TxnField]

    # default constructor
    def __init__(self, field:TxnField):
        self.field = field

    def type_of(self):
        return type_of_field[self.field]
    

class Global(LeafExpr):
    field: ClassVar[GlobalField]

    # default constructor
    def __init__(self, field:GlobalField):
        self.field = field

    def type_of(self):
        return type_of_global_field(self.field)


# ed25519 signature verification
class Ed25519Verify(NaryExpr):
    args: ClassVar[List[str]]

    # default constructor
    def __init__(self, data:str, sig:str, pk:str):
        arg_list = [data, sig, pk]
        self.args = arg_list

    def type_of(self):
        return TealType.uint64
        
