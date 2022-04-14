from .array_static import StaticArray, StaticArrayTypeSpec
from .array_dynamic import DynamicArray, DynamicArrayTypeSpec
from .uint import ByteTypeSpec
from .util import substringForDecoding

from ..int import Int
from ..expr import Expr

address_length = 32


class AddressTypeSpec(StaticArrayTypeSpec):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec(), address_length)

    def new_instance(self) -> "Address":
        return Address()

    def __str__(self) -> str:
        return "address"


AddressTypeSpec.__module__ = "pyteal"


class Address(StaticArray):
    def __init__(self) -> None:
        super().__init__(AddressTypeSpec(), address_length)

    def type_spec(self) -> AddressTypeSpec:
        return AddressTypeSpec()

    def get(self) -> Expr:
        return self.stored_value.load()


Address.__module__ = "pyteal"


class StringTypeSpec(DynamicArrayTypeSpec):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec())

    def new_instance(self) -> "String":
        return String()

    def __str__(self) -> str:
        return "string"


StringTypeSpec.__module__ = "pyteal"


class String(DynamicArray):
    def __init__(self) -> None:
        super().__init__(StringTypeSpec())

    def type_spec(self) -> StringTypeSpec:
        return StringTypeSpec()

    def get(self) -> Expr:
        return substringForDecoding(self.stored_value.load(), startIndex=Int(2))


String.__module__ = "pyteal"
