from typing import Union, Sequence, TypeVar

from pyteal.errors import TealInputError

from pyteal.ast.abi.type import ComputedValue, BaseType
from pyteal.ast.abi.array_static import StaticArray, StaticArrayTypeSpec
from pyteal.ast.abi.uint import ByteTypeSpec
from pyteal.ast.expr import Expr
from pyteal.ast.bytes import Bytes

ADDRESS_LENGTH = 32

T = TypeVar("T", bound=BaseType)
N = TypeVar("N", bound=int)

class AddressTypeSpec(StaticArrayTypeSpec):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec(), ADDRESS_LENGTH)

    def new_instance(self) -> "Address":
        return Address()

    def __str__(self) -> str:
        return "address"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AddressTypeSpec)


AddressTypeSpec.__module__ = "pyteal"


class Address(StaticArray):
    def __init__(self) -> None:
        super().__init__(AddressTypeSpec())

    def type_spec(self) -> AddressTypeSpec:
        return AddressTypeSpec()

    def get(self) -> Expr:
        return self.stored_value.load()

    def set(self, value: Union[Sequence[T], StaticArray[T, N], ComputedValue[StaticArray[T, N]], "Address", str, Expr]):
        
        if isinstance(value, ComputedValue):
            if value.produced_type_spec() is not AddressTypeSpec():
                raise TealInputError(f"Got ComputedValue with type spec {value.produced_type_spec()}, expected AddressTypeSpec")
            return value.store_into(self)

        if isinstance(value, BaseType):
            if value.type_spec() is not AddressTypeSpec():
                raise TealInputError(f"Got {value.__class__} with type spec {value.type_spec()}, expected AddressTypeSpec")
            return self.decode(self.encode())

        if isinstance(value, str):
            return self.stored_value.store(Bytes(value))

        if isinstance(value, Expr):
            return self.stored_value.store(value)

        raise TealInputError(f"Expected str, Address or Expr got {value}")


Address.__module__ = "pyteal"
