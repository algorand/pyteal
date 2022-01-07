from pyteal import Bytes, Concat, Expr, Extract, Int, Len, Seq, TealType

from .abi_type import ABIType
from .uint import Uint16


class String(ABIType):
    stack_type = TealType.bytes
    dynamic = True

    def __init__(self, value: Bytes):
        self.value = value
        self.byte_len = Seq(Len(value) + Int(2))

    @classmethod
    def decode(cls, value: Bytes) -> "String":
        return String(Extract(value, Int(2), Uint16.decode(value)))

    def encode(self) -> Expr:
        return Concat(Uint16(Len(self.value)).encode(), self.value)


class Address(ABIType):
    stack_type = TealType.bytes
    byte_len = Int(32)

    def __init__(self, value: Bytes):
        self.value = value

    @classmethod
    def decode(cls, value: Bytes):
        return Address(value)

    def encode(self) -> Expr:
        return self.value
