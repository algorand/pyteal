from ..unaryexpr import Len
from ..naryexpr import Concat
from ..substring import Extract
from ...types import TealType
from ..expr import Expr
from ..substring import Suffix
from ..int import Int
from .type import Type, substringForDecoding


class String(Type):
    def __init__(self) -> None:
        super().__init__(TealType.bytes)

    def has_same_type_as(self, other: Type) -> bool:
        return type(other) is String

    def is_dynamic(self) -> bool:
        return True

    def get(self) -> Expr:
        return self.stored_value.load()

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        extracted = substringForDecoding(
            encoded, startIndex=startIndex, endIndex=endIndex, length=length
        )
        return self.stored_value.store(extracted)

    def encode(self) -> Expr:
        return Concat(self.length(), self.stored_value.load())

    def length(self) -> Expr:
        return Len(self.value.load())

    def new_instance(self: Type) -> "String":
        return String()

    def byte_length_static(self) -> int:
        raise ValueError("Type is dynamic")

    def __str__(self) -> str:
        return "string"


class Address(Type):
    def __init__(self) -> None:
        super().__init__(TealType.bytes)

    def has_same_type_as(self, other: Type) -> bool:
        return type(other) is Address

    def is_dynamic(self) -> bool:
        return False

    def get(self) -> Expr:
        return self.stored_value.load()

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        return self.stored_value.store(Extract(encoded, Int(0), Int(32)))

    def encode(self) -> Expr:
        return self.stored_value.load()

    def new_instance(self: Type) -> "Address":
        return Address()

    def byte_length_static(self) -> int:
        return 32

    def length(self) -> Expr:
        return Int(self.byte_length_static())

    def __str__(self) -> str:
        return "address"
