from enum import IntEnum
from typing import Union, Sequence, Literal, cast
from collections.abc import Sequence as CollectionSequence

from pyteal.errors import TealInputError

from pyteal.ast.bytes import Bytes
from pyteal.ast.addr import Addr
from pyteal.ast.abi.type import ComputedValue, BaseType
from pyteal.ast.abi.array_static import StaticArray, StaticArrayTypeSpec
from pyteal.ast.abi.uint import ByteTypeSpec, Byte
from pyteal.ast.expr import Expr


class AddressLength(IntEnum):
    String = 58
    Bytes = 32


AddressLength.__module__ = "pyteal"


class AddressTypeSpec(StaticArrayTypeSpec):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec(), AddressLength.Bytes)

    def new_instance(self) -> "Address":
        return Address()

    def annotation_type(self) -> "type[Address]":
        return Address

    def __str__(self) -> str:
        return "address"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AddressTypeSpec)


AddressTypeSpec.__module__ = "pyteal"


class Address(StaticArray[Byte, Literal[AddressLength.Bytes]]):
    def __init__(self) -> None:
        super().__init__(AddressTypeSpec())

    def type_spec(self) -> AddressTypeSpec:
        return AddressTypeSpec()

    def get(self) -> Expr:
        return self.stored_value.load()

    def set(
        self,
        value: Union[
            Sequence[Byte],
            StaticArray[Byte, Literal[AddressLength.Bytes]],
            ComputedValue[StaticArray[Byte, Literal[AddressLength.Bytes]]],
            "Address",
            str,
            bytes,
            Expr,
        ],
    ):

        match value:
            case ComputedValue():
                pts = value.produced_type_spec()
                if pts == AddressTypeSpec() or pts == StaticArrayTypeSpec(
                    ByteTypeSpec(), AddressLength.Bytes
                ):
                    return value.store_into(self)

                raise TealInputError(
                    f"Got ComputedValue with type spec {pts}, expected AddressTypeSpec or StaticArray[Byte, Literal[AddressLength.Bytes]]"
                )
            case BaseType():
                if (
                    value.type_spec() == AddressTypeSpec()
                    or value.type_spec()
                    == StaticArrayTypeSpec(ByteTypeSpec(), AddressLength.Bytes)
                ):
                    return self.stored_value.store(value.stored_value.load())

                raise TealInputError(
                    f"Got {value} with type spec {value.type_spec()}, expected AddressTypeSpec"
                )
            case str():
                # Addr throws if value is invalid address
                return self.stored_value.store(Addr(value))
            case bytes():
                if len(value) == AddressLength.Bytes:
                    return self.stored_value.store(Bytes(value))
                raise TealInputError(
                    f"Got bytes with length {len(value)}, expected {AddressLength.Bytes}"
                )
            case Expr():
                return self.stored_value.store(value)
            case CollectionSequence():
                return super().set(cast(Sequence[Byte], value))

        raise TealInputError(
            f"Got {type(value)}, expected Sequence, StaticArray, ComputedValue, Address, str, bytes, Expr"
        )


Address.__module__ = "pyteal"
