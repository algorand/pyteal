#!/usr/bin/env python3
"""
Operators on uint64

"""

from typing import ClassVar, List
from enum import Enum

from .util import *
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
     
    # default constructor
    def __init__(self, address:str):        
        valid_address(address)
        self.address = address

    def __teal__(self):
        return [["Addr", self.address]]

    def __str__(self):
        return "(address: {})".format(self.address)

    def type_of(self):
        return TealType.bytes


class Bytes(LeafExpr):
     
    #default constructor
    def __init__(self, base:str, byte_str:str):
        if base == "base32":
            self.base = base
            valid_base32(byte_str)
            self.byte_str = byte_str
        elif base == "base64":
            self.base = base
            valid_base64(byte_str)
            self.byte_str = byte_str
        elif base == "base16":
            self.base = base
            if byte_str.startswith("0x"):
                self.byte_str = byte_str[2:]
            else:
                self.byte_str = byte_str
            valid_base16(self.byte_str)
        else:
            raise TealInputError("invalid base {}, need to be base32, base64, or base16.".format(base))


    def __teal__(self):
        if self.base == hex:
            return [["byte", self.byte_str]]
        return [["byte", self.base, self.byte_str]]
        
    def __str__(self):
        return "({} bytes: {})".format(self.base, self.byte_str)

    def type_of(self):
        return TealType.bytes


class Int(LeafExpr):
     
    # default contructor
    def __init__(self, value:int):
        if type(value) is not int:
            raise TealInputError("invalid input type {} to Int".format(
                 type(value)))
 
        if value >= 0 and value < 2 ** 64:
             self.value = value
        else:
            raise TealInputError("Int {} is out of range".format(value))

    def __teal__(self):
        return [["int", str(self.value)]]
       
    def __str__(self):
        return "(Int: {})".format(self.value)

    def type_of(self):
        return TealType.uint64


class Arg(LeafExpr):
     
    # default constructor
    def __init__(self, index:int):
        if type(index) is not int:
            raise TealInputError("invalid arg input type {}".format(
                 type(index)))

        if index < 0 or index > 255:
            raise TealInputError("invalid arg index {}".format(index))

        self.index = index

    def __teal__(self):
        return [["arg", str(self.index)]]
        
    def __str__(self):
        return "(arg {})".format(self.index)

    def type_of(self):
        return TealType.bytes


class And(BinaryExpr):

    # default constructor
    def __init__(self, left:Expr, right:Expr):
         require_type(left.type_of(), TealType.uint64)
         require_type(right.type_of(), TealType.uint64)
         self.left = left
         self.right = right

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [["&&"]]

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

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [["||"]]
        
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

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [["<"]]
         
    def __str__(self):
        return "(< {} {})".format(self.left, self.right)

    def type_of(self):
        return TealType.uint64


# less than
class Gt(BinaryExpr):

    # default constructor
    def __init__(self, left:Expr, right:Expr):
        require_type(left.type_of(), TealType.uint64)
        require_type(right.type_of(), TealType.uint64) 
        self.left = left
        self.right = right

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [[">"]]

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

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [["="]]
        
    def __str__(self):
         return "(== {} {})".format(self.left, self.right)
    
    def type_of(self):
        return TealType.uint64
   
    
# return the length of a bytes value
class Len(UnaryExpr):

    # default constructor
    def __init__(self, child:Expr):
        require_type(child.type_of(), TealType.bytes)
        self.child = child

    def __teal__(self):
        return self.child.__teal__() + [["len"]]
         
    def __str__(self):
         return "(len {})".format(self.child)

    def type_of(self):
        return TealType.uint64
   

# get a field from the current txn
class Txn(LeafExpr):

    # default constructor
    def __init__(self, field:TxnField):
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

    @classmethod
    def sender_balance(cls):
        return cls(TxnField.sender_balance)

    @classmethod
    def lease(cls):
        return cls(TxnField.lease)
   
    def type_of(self):
        return type_of_field[self.field]
   

class Global(LeafExpr):

    # default constructor
    def __init__(self, field:GlobalField):
        self.field = field

    def __teal__(self):
        return [["global", str_of_global_field[self.field]]]
         
    def __str__(self):
        return "(Global {})".format(str_of_global_field[self.field])

    @classmethod
    def round(cls):
        return cls(GlobalField.round)

    @classmethod
    def min_txn_fee(cls):
        return cls(GlobalField.min_txn_fee)

    @classmethod
    def min_balance(cls):
        return cls(GlobalField.min_balance)

    @classmethod
    def max_txn_life(cls):
        return cls(GlobalField.max_txn_life)

    @classmethod
    def time_stamp(cls):
        return cls(GlobalField.time_stamp)

    @classmethod
    def zero_address(cls):
        return cls(GlobalField.zero_address)

    @classmethod
    def group_size(cls):
        return cls(GlobalField.group_size)

    def type_of(self):
        return type_of_global_field[self.field]


# ed25519 signature verification
class Ed25519Verify(NaryExpr):

    # default constructor
    def __init__(self, arg0:Expr, arg1:Expr, arg2:Expr):
        require_type(arg0.type_of(), TealType.bytes)
        require_type(arg1.type_of(), TealType.bytes)
        require_type(arg2.type_of(), TealType.bytes)
         
        self.args = [arg0, arg1, arg2]

    def __teal__(self):
        return self.args[0].__teal__() + \
               self.args[1].__teal__() + \
               self.args[2].__teal__() + \
               [["ed25519verify"]]

    def __str__(self):
        return "(ed25519verify {} {} {})".format(self.args[0],
                                                 self.args[1], self.args[2])
    
    def type_of(self):
        return TealType.uint64


class Gtxn(LeafExpr):

        # default constructor
    def __init__(self, field:TxnField):
        self.field = field

    def __str__(self):
        return "(Gtxn {})".format(str_of_field[self.field])

    def __teal__(self):
        return [["gtxn", str_of_field[self.field]]]
   
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

    @classmethod
    def sender_balance(cls):
        return cls(TxnField.sender_balance)

    @classmethod
    def lease(cls):
        return cls(TxnField.lease)
   
    def type_of(self):
        return type_of_field[self.field]


class Ite(NaryExpr):

    #default constructor
    def __init__(self, arg0:Expr, arg1:Expr, arg2:Expr):
        require_type(arg0.type_of(), TealType.uint64)
        require_type(arg2.type_of(), arg1.type_of())

        self.args = [arg0, arg1, arg2]

    def __teal__(self):
        cond = self.args[0].__teal__()
        l1 = new_label()
        t_branch = self.args[1].__teal__()
        e_branch = self.args[2].__teal__()
        l2 = new_label()
        # TODO: remove pop if teal check is removed
        ret = cond + [["bnz", l1]] + e_branch + [["int", "1"]] + \
              [["bnz", l2], ["pop"], [l1]] + t_branch + [[l2]]  

    def __str__(self):
        return "(Ite {} {} {})".format(self.args[0], self.args[1], self.args[2])

    def type_of(self):
        return type_of(self.args[1])
