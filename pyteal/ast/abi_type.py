from abc import abstractmethod

from . import Bytes, Expr
from ..types import TealType
from ..compiler import CompileOptions


class ABIType(Expr):
    byte_len: Expr
    value: Expr

    stack_type = TealType.bytes
    dynamic = False

    @abstractmethod
    def encode(self) -> Expr:
        pass

    @abstractmethod
    def decode(self, value: Expr) -> "ABIType":
        pass

    def type_of(self) -> "TealType":
        return self.stack_type

    def has_return(self) -> bool:
        return True

    def __str__(self) -> str:
        return ""

    def __teal__(self, options: "CompileOptions"):
        return self.value.__teal__(options)
