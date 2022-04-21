from pyteal.ast.abi.array_static import StaticArray, StaticArrayTypeSpec
from pyteal.ast.abi.uint import ByteTypeSpec
from pyteal.ast.expr import Expr

ADDRESS_LENGTH = 32


class AddressTypeSpec(StaticArrayTypeSpec):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec(), ADDRESS_LENGTH)

    def new_instance(self) -> "Address":
        return Address()

    def __str__(self) -> str:
        return "address"


AddressTypeSpec.__module__ = "pyteal"


class Address(StaticArray):
    def __init__(self) -> None:
        super().__init__(AddressTypeSpec(), ADDRESS_LENGTH)

    def type_spec(self) -> AddressTypeSpec:
        return AddressTypeSpec()

    def get(self) -> Expr:
        return self.stored_value.load()


Address.__module__ = "pyteal"
