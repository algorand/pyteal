#!/usr/bin/env python3

"""
An expression language for TEAL.

"""

from abc import ABCMeta, abstractmethod

class Expr(Printable):
     __metaclass__ = ABCMeta

class BinaryExpr(Expr):
    pass

class UnaryExpr(Expr):
    pass
