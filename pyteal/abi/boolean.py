from pyteal import *
from .utils import suffix
from .abi_type import ABIType


class Boolean(ABIType):
    stack_type = TealType.bytes
    byte_len = Int(1)

    def __init__(self, value: bool):
        pass

    def decode(self, value: Bytes):
        pass

    def encode(self, value: Bytes):
        pass
