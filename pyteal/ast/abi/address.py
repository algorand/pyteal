from typing import Union

from pyteal.errors import TealInputError

from .type import ComputedValue
from .array_static import StaticArray, StaticArrayTypeSpec
from .uint import ByteTypeSpec

from ..bytes import Bytes
from .array_static import StaticArray, StaticArrayTypeSpec
from .uint import ByteTypeSpec
from ..expr import Expr

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

    def set(self, value: Union[str, "Address", ComputedValue["Address"], Expr]) -> Expr:
        if isinstance(value, ComputedValue):
            return value.store_into(self)

        if isinstance(value, Address):
            return self.decode(self.encode())

        if isinstance(value, str):
            return self.stored_value.store(Bytes(str))

        if isinstance(value, Expr):
            return self.stored_value.store(value)

        raise TealInputError(f"Expected str, Address or Expr got {value}")


Address.__module__ = "pyteal"
