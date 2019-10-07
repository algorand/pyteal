#!/usr/bin/env python3
"""
Helper functions and classes
"""

from enum import Enum

class TealType(Enum):
     uint64 = 0
     bytes = 1
     anytype = 2

class TealTypeError(Exception):

    def __init__(self, actual, expected):
        self.message = "Type error: {} while expected {} ".format(acutal, expected)


class TealTypeMismatchError(Exception):
    
    def __init__(self, t1, t2):
        self.message = "Type mismatch error: {} cannot be resolved to {}".format(t1, t2)


def require_type(actual: TealType, expected: TealType):
    if acutal != expected:
        raise TealTypeError(actual, expected)
