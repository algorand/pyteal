from typing import Union, Sequence, TypeVar

from pyteal.errors import TealInputError

from pyteal.ast.bytes import Bytes
from pyteal.ast.addr import Addr
from pyteal.ast.abi.type import ComputedValue, BaseType
from pyteal.ast.abi.array_static import StaticArray, StaticArrayTypeSpec
from pyteal.ast.abi.uint import ByteTypeSpec
from pyteal.ast.expr import Expr

ADDRESS_LENGTH_STR = 58
ADDRESS_LENGTH_BYTES = 32

T = TypeVar("T", bound=BaseType)
N = TypeVar("N", bound=int)


class AddressTypeSpec(StaticArrayTypeSpec):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec(), ADDRESS_LENGTH_BYTES)

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

    def set(
        self,
        value: Union[
            Sequence[T],
            StaticArray[T, N],
            ComputedValue[StaticArray[T, N]],
            "Address",
            str,
            bytes,
            Expr,
        ],
    ):

        if isinstance(value, ComputedValue):
            if not isinstance(value.produced_type_spec(), AddressTypeSpec):
                raise TealInputError(
                    f"Got ComputedValue with type spec {value.produced_type_spec()}, expected AddressTypeSpec"
                )
            return value.store_into(self)

        elif isinstance(value, BaseType):

            if isinstance(value.type_spec(), AddressTypeSpec):
                return self.decode(value.encode())

            if (
                isinstance(value.type_spec(), StaticArrayTypeSpec)
                and isinstance(value.type_spec().value_type_spec(), ByteTypeSpec)
                and value.type_spec().length_static() == ADDRESS_LENGTH_BYTES
            ):
                return self.decode(value.encode())

            raise TealInputError(
                f"Got {value} with type spec {value.type_spec()}, expected AddressTypeSpec"
            )

        elif isinstance(value, str) and len(value) == ADDRESS_LENGTH_STR:
            return self.stored_value.store(Addr(value))

        elif isinstance(value, bytes) and len(value) == ADDRESS_LENGTH_BYTES:
            return self.stored_value.store(Bytes(value))

        elif isinstance(value, Expr):
            return self.stored_value.store(value)

        elif isinstance(value, Sequence):
            return super().set(value)

        raise TealInputError(
            f"Got {value}, expected str, bytes, Expr, Sequence, Address, or ComputedType"
        )


Address.__module__ = "pyteal"
