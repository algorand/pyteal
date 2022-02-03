from typing import Union, cast

from ...types import TealType
from ..expr import Expr
from ..int import Int
from ..bytes import Bytes
from ..unaryexpr import Len
from ..substring import Extract
from ..naryexpr import Concat
from ..seq import Seq

from .type import Type
from .uint import Uint16


# class String(ABIType):
#     stack_type = TealType.bytes
#     dynamic = True

#     def __init__(self, value: Union[str, Expr]):
#         if type(value) == str:
#             value = Bytes(value)

#         value = cast(Expr, value)
#         self.value = value
#         self.byte_len = Seq(Len(value) + Int(2))

#     @classmethod
#     def decode(cls, value: Expr) -> "String":
#         return String(Extract(value, Int(2), Uint16.decode(value)))

#     def encode(self) -> Expr:
#         return Concat(Uint16(Len(self.value)).encode(), self.value)


# String.__module__ = "pyteal"


# class Address(ABIType):
#     stack_type = TealType.bytes
#     byte_len = Int(32)

#     def __init__(self, value: Expr):
#         self.value = value

#     @classmethod
#     def decode(cls, value: Expr) -> "Address":
#         return Address(value)

#     def encode(self) -> Expr:
#         return self.value


# Address.__module__ = "pyteal"
