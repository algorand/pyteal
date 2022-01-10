from abc import abstractmethod

from . import Bytes, Expr


class ABIType(Expr):
    dynamic = False

    byte_len: Expr

    @abstractmethod
    def encode(self) -> Expr:
        pass

    @abstractmethod
    def decode(self, value: Bytes) -> "ABIType":
        pass

    def type_of(self) -> "TealType":
        return self.stack_type

    def has_return(self) -> bool:
        return True

    def __str__(self) -> str:
        return ""

    def __teal__(self, options: "CompileOptions"):
        return self.value.__teal__(options)
