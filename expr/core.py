#!/usr/bin/env python3

"""
An expression language for TEAL.

"""

from abc import ABC, abstractmethod
from enum import Enum

class TealType(Enum):
     uint64 = 0
     bytes = 1
     anytype = 2

     
class Expr(ABC):

     @abstractmethod
     def type_of(self) -> TealType:
          """Returns a TealType enum describing the expression's return type
          """
          pass

class BinaryExpr(Expr):
     pass 
    

class UnaryExpr(Expr):
     pass

class NaryExpr(Expr):
     pass

class LeafExpr(Expr):
     pass

