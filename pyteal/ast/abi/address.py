from enum import Enum
from typing import Union, Sequence, Literal
from collections.abc import Sequence as CollectionSequence

from pyteal.errors import TealInputError

from pyteal.ast.bytes import Bytes
from pyteal.ast.addr import Addr
from pyteal.ast.abi.type import ComputedValue, BaseType
from pyteal.ast.abi.array_static import StaticArray, StaticArrayTypeSpec
from pyteal.ast.abi.uint import ByteTypeSpec, Byte
from pyteal.ast.expr import Expr


class AddressLength(Enum):
    String = 58
    Bytes = 32


AddressLength.__module__ = "pyteal"


class AddressTypeSpec(StaticArrayTypeSpec):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec(), AddressLength.Bytes.value)

    def new_instance(self) -> "Address":
        return Address()

    def __str__(self) -> str:
        return "address"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AddressTypeSpec)


AddressTypeSpec.__module__ = "pyteal"


class Address(StaticArray[Byte, Literal[32]]):
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
            StaticArray[Byte, Literal[32]],
            ComputedValue[StaticArray[Byte, Literal[32]]],
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
                    ByteTypeSpec(), AddressLength.Bytes.value
                ):
                    return value.store_into(self)

                raise TealInputError(
                    f"Got ComputedValue with type spec {pts}, expected AddressTypeSpec or StaticArray[Byte, Literal[32]]"
                )
            case BaseType():
                if (
                    value.type_spec() == AddressTypeSpec()
                    or value.type_spec()
                    == StaticArrayTypeSpec(ByteTypeSpec(), AddressLength.Bytes.value)
                ):
                    return self.stored_value.store(value.stored_value.load())

                raise TealInputError(
                    f"Got {value} with type spec {value.type_spec()}, expected AddressTypeSpec"
                )
            case str():
                if len(value) == AddressLength.String.value:
                    return self.stored_value.store(Addr(value))
                raise TealInputError(
                    f"Got string with length {len(value)}, expected {AddressLength.String.value}"
                )
            case bytes():
                if len(value) == AddressLength.Bytes.value:
                    return self.stored_value.store(Bytes(value))
                raise TealInputError(
                    f"Got bytes with length {len(value)}, expected {AddressLength.Bytes.value}"
                )
            case Expr():
                return self.stored_value.store(value)
            case CollectionSequence():
                # TODO: mypy thinks its possible for the type of `value` here to be
                # Union[Sequence[Byte], str, bytes] even though we check above?
                if isinstance(value, str) or isinstance(value, bytes):
                    return
                return super().set(value)

        # TODO: wdyt? something like this maybe should be in utils? or just manually update the args each time?
        # from inspect import signature
        # from typing import get_args
        # sig = signature(self.set)
        # expected = ", ".join([repr(a) for a in get_args(sig.parameters['value'].annotation)])
        # raise TealInputError(
        #     f"Got {type(value)}, expected {expected}"
        # )

        raise TealInputError(
            f"Got {type(value)}, expected Sequence, StaticArray, ComputedValue, Address, str, bytes, Expr"
        )


Address.__module__ = "pyteal"
