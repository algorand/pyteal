#!/usr/bin/env python3
"""
Helper functions and classes
"""

from enum import Enum
import re

class TealType(Enum):
     uint64 = 0
     bytes = 1
     anytype = 2

class TealTypeError(Exception):

    def __init__(self, actual, expected):
        self.message = "Type error: {} while expected {} ".format(actual, expected)


class TealTypeMismatchError(Exception):
    
    def __init__(self, t1, t2):
        self.message = "Type mismatch error: {} cannot be resolved to {}".format(t1, t2)


class TealInputError(Exception):

     def __init__(self, msg):
        self.message = "Input error: {}".format(msg)
        

def require_type(actual: TealType, expected: TealType):
    if actual != expected:
        raise TealTypeError(actual, expected)


def valid_address(address:str):
    """ check if address is a valid address with checksum
    """
    if type(address) is not str:
        raise TealInputError("An address needs to be a string")

    if len(address) != 58:
        raise TealInputError("Address length is not correct. Should \
            be a base 32 string encoded 32 bytes public key + 4 bytes checksum")

    pattern = re.compile(r'[A-Z2-9]*') # RFC 4648 base 32 w/o padding 

    if pattern.fullmatch(address) is None:
        raise TealInputError("The input to Addr needs to be a RFC 4648 base 32 \
             encoding string without padding.")
