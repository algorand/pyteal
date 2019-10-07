#!/usr/bin/env python3
"""
Operators on uint64

"""

from core import Expr, BinaryExpr, UnaryExpr, LeafExpr, TealType
from typing import ClassVar

class Addr(LeafExpr):
    address: ClassVar[str]
    
    # default constructor
    def __init__(self, address:str):        
        #TODO: check the validity of the address
        self.address = address
        
    def typeof(self):
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

    def typeof(self):
        return TealType.raw_bytes


class Arg(LeafExpr):
    index: ClassVar[int]

    #default constructor
    def __init__(self, index:int):
        if index < 0 or index > 255:
            raise "Invalid arg index: {}".format(index)

        self.index = index

    def typeof(self):
        return TealType.raw_bytes


class And(BinaryExpr):
    left: ClassVar[Expr]
    right: ClassVar[Expr]

    #default constructor
    def __init__(self, left:Expr, right:Expr):
        self.left = left
        self.right = right

    def typeof(self):
        return TealType.uint64
