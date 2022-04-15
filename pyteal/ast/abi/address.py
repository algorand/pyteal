from .array_static import StaticArray, StaticArrayTypeSpec
from .uint import ByteTypeSpec
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
