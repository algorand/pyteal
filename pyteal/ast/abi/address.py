from enum import IntEnum
from typing import Union, Sequence, Literal, cast
from collections.abc import Sequence as CollectionSequence

from pyteal.errors import TealInputError

from pyteal.ast.assert_ import Assert
from pyteal.ast.bytes import Bytes
from pyteal.ast.int import Int
from pyteal.ast.seq import Seq
from pyteal.ast.unaryexpr import Len
from pyteal.ast.addr import Addr
from pyteal.ast.abi.type import ComputedValue, BaseType
from pyteal.ast.abi.array_static import StaticArray, StaticArrayTypeSpec
from pyteal.ast.abi.uint import ByteTypeSpec, Byte
from pyteal.ast.expr import Expr


class AddressLength(IntEnum):
    String = 58
    Bytes = 32


AddressLength.__module__ = "pyteal.abi"


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


AddressTypeSpec.__module__ = "pyteal.abi"


class Address(StaticArray[Byte, Literal[AddressLength.Bytes]]):
    def __init__(self) -> None:
        super().__init__(AddressTypeSpec())

    def type_spec(self) -> AddressTypeSpec:
        return AddressTypeSpec()

    def get(self) -> Expr:
        """Return the 32-byte value held by this Address as a PyTeal expression.

        The expression will have the type TealType.bytes.
        """
        return self.stored_value.load()

    def set(
        self,
        value: Union[
            str,
            bytes,
            Expr,
            Sequence[Byte],
            StaticArray[Byte, Literal[AddressLength.Bytes]],
            ComputedValue[StaticArray[Byte, Literal[AddressLength.Bytes]]],
            "Address",
            ComputedValue["Address"],
        ],
    ):
        """Set the value of this Address to the input value.

        The behavior of this method depends on the input argument type:

            * :code:`str`: set the value to the address from the encoded address string. This string must be a valid 58-character base-32 Algorand address with checksum.
            * :code:`bytes`: set the value to the raw address bytes. This byte string must have length 32.
            * :code:`Expr`: set the value to the result of a PyTeal expression, which must evaluate to a TealType.bytes. The program will fail if the evaluated byte string length is not 32.
            * :code:`Sequence[Byte]`: set the bytes of this Address to those contained in this Python sequence (e.g. a list or tuple). A compiler error will occur if the sequence length is not 32.
            * :code:`StaticArray[Byte, 32]`: copy the bytes from a StaticArray of 32 bytes.
            * :code:`ComputedValue[StaticArray[Byte, 32]]`: copy the bytes from a StaticArray of 32 bytes produced by a ComputedValue.
            * :code:`Address`: copy the value from another Address.
            * :code:`ComputedValue[Address]`: copy the value from an Address produced by a ComputedValue.

        Args:
            value: The new value this Address should take. This must follow the above constraints.

        Returns:
            An expression which stores the given value into this Address.
        """

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
                return Seq(
                    self.stored_value.store(value),
                    Assert(
                        Len(self.stored_value.load()) == Int(AddressLength.Bytes.value)
                    ),
                )
            case CollectionSequence():
                if len(value) != AddressLength.Bytes:
                    raise TealInputError(
                        f"Got bytes with length {len(value)}, expected {AddressLength.Bytes}"
                    )
                return super().set(cast(Sequence[Byte], value))

        raise TealInputError(
            f"Got {type(value)}, expected Sequence, StaticArray, ComputedValue, Address, str, bytes, Expr"
        )


Address.__module__ = "pyteal.abi"
