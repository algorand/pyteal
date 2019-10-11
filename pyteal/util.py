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

    def __str__(self):
        return self.message
        

class TealTypeMismatchError(Exception):
    
    def __init__(self, t1, t2):
        self.message = "Type mismatch error: {} cannot be resolved to {}".format(t1, t2)

    def __str__(self):
        return self.message


class TealInputError(Exception):

    def __init__(self, msg):
        self.message = "Input error: {}".format(msg)

    def __str__(self):
        return self.message
        
        
def require_type(actual: TealType, expected: TealType):
    if actual != expected:
        raise TealTypeError(actual, expected)


def valid_address(address:str):
    """ check if address is a valid address with checksum
    """
    if type(address) is not str:
        raise TealInputError("An address needs to be a string")

    if len(address) != 58:
        raise TealInputError("Address length is not correct. Should " +
            "be a base 32 string encoded 32 bytes public key + 4 bytes checksum")

    valid_base32(address)
    


def valid_base32(s:str):
    """ check if s is a valid base32 encoding string
    """
    pattern = re.compile(r'[A-Z2-9]*') # RFC 4648 base 32 w/o padding

    if pattern.fullmatch(s) is None:
        raise TealInputError("{} is not a valid RFC 4648 base 32 string".format( 
            s))


def valid_base64(s:str):
    """ check if s is a valid base64 encoding string
    """
    pattern = re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$')

    if pattern.fullmatch(s) is None:
        raise TealInputError("{} is not a valid RFC 4648 base 64 string".format(
             s))

def valid_base16(s:str):
    """ check if s is a valid hex encoding string
    """
    pattern = re.compile(r'[0-9ZA-F]*')

    if pattern.fullmatch(s) is None:
        raise TealInputError("{} is not a valid RFC 4648 base 16 string".format(
             s))
         
