#!/usr/bin/env python3

"""
An expression language for TEAL.

"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar, List

from .util import TealType

     
class Expr(ABC):

     @abstractmethod
     def type_of(self) -> TealType:
          """Returns a TealType enum describing the expression's return type
          """
          pass

class BinaryExpr(Expr):
     left: ClassVar[Expr]
     right: ClassVar[Expr]
    

class UnaryExpr(Expr):
     child: ClassVar[Expr]

class NaryExpr(Expr):
     args: ClassVar[List[Expr]]

class LeafExpr(Expr):
     pass

