#!/usr/bin/env python3

"""
Operators on uint64

"""

from typing import ClassVar, List
from enum import Enum
from functools import reduce

from .util import *
from .config import *
from .expr import Expr, BinaryExpr, UnaryExpr, NaryExpr, LeafExpr, TealType


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


class GlobalField(Enum):
     min_txn_fee = 0
     min_balance = 1
     max_txn_life = 2
     zero_address = 3
     group_size = 4


type_of_global_field = {
     GlobalField.min_txn_fee: TealType.uint64,
     GlobalField.min_balance: TealType.uint64,
     GlobalField.max_txn_life: TealType.uint64,
     GlobalField.zero_address: TealType.bytes,
     GlobalField.group_size: TealType.uint64
}


str_of_global_field = {
     GlobalField.min_txn_fee: "MinTxnFee",
     GlobalField.min_balance: "MinBalance",
     GlobalField.max_txn_life: "MaxTxnLife",
     GlobalField.zero_address: "ZeroAddress",
     GlobalField.group_size: "GroupSize"
}


class Tmpl(LeafExpr):

    # default constrcutor
    def __init__(self, tmpl_v:str) -> None:
        valid_tmpl(tmpl_v)
        self.name = tmpl_v

    def __str__(self):
        return self.name

    def __teal__(self):
        raise TealInternalError("Tmpl is not expected here")

    def type_of(self):
        raise TealInternalError("Tmpl is not expected here")

class Addr(LeafExpr):
     
    # default constructor
    def __init__(self, address) -> None:        
        if isinstance(address, Tmpl):
            self.address = address.name
        else:
            valid_address(address)
            self.address = address

    def __teal__(self):
        return [["addr", self.address]]

    def __str__(self):
        return "(address: {})".format(self.address)

    def type_of(self):
        return TealType.bytes


class Bytes(LeafExpr):
     
    #default constructor
    def __init__(self, base:str, byte_str) -> None:
        if base == "base32":
            self.base = base
            if isinstance(byte_str, Tmpl):
                self.byte_str = byte_str.name
            else:
                valid_base32(byte_str)
                self.byte_str = byte_str
        elif base == "base64":
            self.base = base
            if isinstance(byte_str, Tmpl):
                self.byte_str = byte_str.name
            else:
                self.byte_str = byte_str
                valid_base64(byte_str)
        elif base == "base16":
            self.base = base
            if isinstance(byte_str, Tmpl):
                self.byte_str = byte_str.name
            elif byte_str.startswith("0x"):
                self.byte_str = byte_str[2:]
                valid_base16(self.byte_str)
            else:
                self.byte_str = byte_str
                valid_base16(self.byte_str)
        else:
            raise TealInputError("invalid base {}, need to be base32, base64, or base16.".format(base))

    def __teal__(self):
        if self.base != "base16":
            return [["byte", self.base, self.byte_str]]
        else:
            return [["byte", "0x" + self.byte_str]]
        
    def __str__(self):
        return "({} bytes: {})".format(self.base, self.byte_str)

    def type_of(self):
        return TealType.bytes


class Int(LeafExpr):
     
    # default contructor
    def __init__(self, value):
        if isinstance(value, Tmpl):
            self.value = value.name
        elif type(value) is not int:
            raise TealInputError("invalid input type {} to Int".format(
                 type(value))) 
        elif value >= 0 and value < 2 ** 64:
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
    def __init__(self, index:int) -> None:
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
    def __init__(self, *argv):
        if len(argv) < 2:
            raise TealInputError("And requires at least two children.")
        for arg in argv:
            if not isinstance(arg, Expr):
                raise TealInputError("{} is not a pyteal expression.".format(arg))
            require_type(arg.type_of(), TealType.uint64)

        self.args = argv
        

    def __teal__(self):
        code = []
        for i, a in enumerate(self.args):
            if i == 0:
                code = a.__teal__()
            else:
                code = code + a.__teal__() +[["&&"]]
        return code

    def __str__(self):
        ret_str = "(And"
        for a in self.args:
            ret_str += " " + a.__str__()
        ret_str += ")"
        return ret_str
        
    def type_of(self):
        return TealType.uint64


class Or(BinaryExpr):

    # default constructor
    def __init__(self, *argv):
        if len(argv) < 2:
            raise TealInputError("Or requires at least two children.")
        for arg in argv:
            if not isinstance(arg, Expr):
                raise TealInputError("{} is not a pyteal expression.".format(arg))
            require_type(arg.type_of(), TealType.uint64)

        self.args = argv

    def __teal__(self):
        code = []
        for i, a in enumerate(self.args):
            if i == 0:
                code = a.__teal__()
            else:
                code = code + a.__teal__() +[["||"]]
        return code
        
    def __str__(self):
        ret_str = "(Or"
        for a in self.args:
            ret_str += " " + a.__str__()
        ret_str += ")"
        return ret_str 

    def type_of(self):
        return TealType.uint64
   

# less than
class Lt(BinaryExpr):

    # default constructor
    def __init__(self, left:Expr, right:Expr) -> None:
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
    def __init__(self, left:Expr, right:Expr) -> None:
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


class Ge(BinaryExpr):

    # default constructor
    def __init__(self, left:Expr, right:Expr) -> None:
        require_type(left.type_of(), TealType.uint64)
        require_type(right.type_of(), TealType.uint64) 
        self.left = left
        self.right = right

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [[">="]]

    def __str__(self):
        return "(>= {} {})".format(self.left, self.right)
   
    def type_of(self):
        return TealType.uint64
   

class Le(BinaryExpr):

    # default constructor
    def __init__(self, left:Expr, right:Expr) -> None:
        require_type(left.type_of(), TealType.uint64)
        require_type(right.type_of(), TealType.uint64) 
        self.left = left
        self.right = right

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [["<="]]

    def __str__(self):
        return "(<= {} {})".format(self.left, self.right)
   
    def type_of(self):
        return TealType.uint64
   
   
# a polymorphic eq
class Eq(BinaryExpr):

    # default constructor
    def __init__(self, left:Expr, right:Expr) -> None:
         # type checking
        t1 = left.type_of()
        t2 = right.type_of()
        if t1 != t2:
            raise TealTypeMismatchError(t1, t2)

        self.left = left
        self.right = right

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [["=="]]
        
    def __str__(self):
         return "(== {} {})".format(self.left, self.right)
    
    def type_of(self):
        return TealType.uint64
   
    
# return the length of a bytes value
class Len(UnaryExpr):

    # default constructor
    def __init__(self, child:Expr) -> None:
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
   

class Global(LeafExpr):

    # default constructor
    def __init__(self, field:GlobalField) -> None:
        self.field = field

    def __teal__(self):
        return [["global", str_of_global_field[self.field]]]
         
    def __str__(self):
        return "(Global {})".format(str_of_global_field[self.field])

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
    def __init__(self, arg0:Expr, arg1:Expr, arg2:Expr) -> None:
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


class If(NaryExpr):

    #default constructor
    def __init__(self, arg0:Expr, arg1:Expr, arg2:Expr) -> None:
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
              [["bnz", l2], ["pop"], [l1+":"]] + t_branch + [[l2+":"]]
        return ret

    def __str__(self):
        return "(If {} {} {})".format(self.args[0], self.args[1], self.args[2])

    def type_of(self):
        return self.args[1].type_of()


class Add(BinaryExpr):

    def __init__(self, left:Expr, right:Expr) -> None:
        require_type(left.type_of(), TealType.uint64)
        require_type(right.type_of(), TealType.uint64)
        self.left = left
        self.right = right

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [["+"]]
         
    def __str__(self):
        return "(+ {} {})".format(self.left, self.right)

    def type_of(self):
        return TealType.uint64
          

class Minus(BinaryExpr):

    def __init__(self, left:Expr, right:Expr) -> None:
        require_type(left.type_of(), TealType.uint64)
        require_type(right.type_of(), TealType.uint64)
        self.left = left
        self.right = right

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [["-"]]
         
    def __str__(self):
        return "(- {} {})".format(self.left, self.right)

    def type_of(self):
        return TealType.uint64


class Mul(BinaryExpr):

    def __init__(self, left:Expr, right:Expr) -> None:
        require_type(left.type_of(), TealType.uint64)
        require_type(right.type_of(), TealType.uint64)
        self.left = left
        self.right = right

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [["*"]]
         
    def __str__(self):
        return "(* {} {})".format(self.left, self.right)

    def type_of(self):
        return TealType.uint64

class Div(BinaryExpr):
    
    def __init__(self, left:Expr, right:Expr) -> None:
        require_type(left.type_of(), TealType.uint64)
        require_type(right.type_of(), TealType.uint64)
        self.left = left
        self.right = right

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [["/"]]
         
    def __str__(self):
        return "(/ {} {})".format(self.left, self.right)

    def type_of(self):
        return TealType.uint64


class Mod(BinaryExpr):

    def __init__(self, left:Expr, right:Expr) -> None:
        require_type(left.type_of(), TealType.uint64)
        require_type(right.type_of(), TealType.uint64)
        self.left = left
        self.right = right

    def __teal__(self):
        return self.left.__teal__() + self.right.__teal__() + [["%"]]
         
    def __str__(self):
        return "(/ {} {})".format(self.left, self.right)

    def type_of(self):
        return TealType.uint64


class Btoi(UnaryExpr):

    # default constructor
    def __init__(self, child:Expr) -> None:
        require_type(child.type_of(), TealType.bytes)
        self.child = child

    def __teal__(self):
        return self.child.__teal__() + [["btoi"]]
         
    def __str__(self):
         return "(btoi {})".format(self.child)

    def type_of(self):
        return TealType.uint64


class Itob(UnaryExpr):

    # default constructor
    def __init__(self, child:Expr) -> None:
        require_type(child.type_of(), TealType.uint64)
        self.child = child

    def __teal__(self):
        return self.child.__teal__() + [["itob"]]
         
    def __str__(self):
         return "(itob {})".format(self.child)

    def type_of(self):
        return TealType.bytes


class Keccak256(UnaryExpr):    

    # default constructor
    def __init__(self, child:Expr) -> None:
        require_type(child.type_of(), TealType.bytes)
        self.child = child

    def __teal__(self):
        return self.child.__teal__() + [["keccak256"]]
         
    def __str__(self):
         return "(keccak {})".format(self.child)

    def type_of(self):
        return TealType.bytes


class Sha512_256(UnaryExpr):    

    # default constructor
    def __init__(self, child:Expr) -> None:
        require_type(child.type_of(), TealType.bytes)
        self.child = child

    def __teal__(self):
        return self.child.__teal__() + [["sha512_256"]]
         
    def __str__(self):
         return "(sha512_256 {})".format(self.child)

    def type_of(self):
        return TealType.bytes


class Sha256(UnaryExpr):   

    # default constructor
    def __init__(self, child:Expr) -> None:
        require_type(child.type_of(), TealType.bytes)
        self.child = child

    def __teal__(self):
        return self.child.__teal__() + [["sha256"]]
         
    def __str__(self):
         return "(sha256 {})".format(self.child)

    def type_of(self):
        return TealType.bytes    


class Nonce(UnaryExpr):

    #default constructor
    def __init__(self, base:str, nonce:str, child:Expr) -> None:
        self.child = child
        self.nonce_bytes = Bytes(base, nonce)

    def __teal__(self):
        return self.nonce_bytes.__teal__() + [["pop"]] + self.child.__teal__()
        
    def __str__(self):
        return "({} nonce: {}) {}".format(self.base, self.nonce, self.child.__str__())

    def type_of(self):
        return self.child.type_of()


class Err(LeafExpr):
    """
    only used internally, not a user facing operator
    """

    #default constructor
    def __init__(self):
        pass

    def __teal__(self):
        return [["err"]]

    def __str__(self):
        return "(err)"

    def type_of(self):
        return TealType.anytype
    

class Cond(NaryExpr):

    # default constructor
    def __init__(self, *argv):

        if len(argv) < 1:
            raise TealInputError("Cond requires at least one [condition, value]")

        value_type = 0

        for arg in argv:
            msg = "Cond should be in the form of Cond([cond1, value1], [cond2, value2], ...), error in {}"
            if not isinstance(arg, list):
                raise TealInputError(msg.format(arg))
            if len(arg) != 2:
                raise TealInputError(msg.format(arg))
            
            require_type(arg[0].type_of(), TealType.uint64) # cond_n should be int

            if value_type == 0: # the types of all branches should be the same
                value_type = arg[1].type_of()
            else:
                require_type(arg[1].type_of(), value_type)

        self.value_type = value_type        
        self.args = argv        

    def __teal__(self):
        # converting cond to if first
        def make_if(conds):
            if len(conds) == 0:
                return Err()
            else:
                e = conds[0]
                return If(e[0], e[1], make_if(conds[1:]))

        desugared = make_if(self.args)
        return desugared.__teal__() 

    def __str__(self):
        ret_str = "(Cond"
        for a in self.args:
            ret_str += " [" + a[0].__str__() + ", " + a[1].__str__() + "]"
        ret_str += ")"
        return ret_str
        
    def type_of(self):
        return self.value_type
