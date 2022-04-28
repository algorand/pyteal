from typing import Union, TypeVar, Sequence

from pyteal.ast.abi.type import ComputedValue, BaseType
from pyteal.ast.abi.array_dynamic import DynamicArray, DynamicArrayTypeSpec
from pyteal.ast.abi.uint import ByteTypeSpec, Uint16TypeSpec

from pyteal.ast.int import Int
from pyteal.ast.expr import Expr
from pyteal.ast.bytes import Bytes
from pyteal.ast.unaryexpr import Itob, Len
from pyteal.ast.substring import Suffix
from pyteal.ast.naryexpr import Concat

from pyteal.errors import TealInputError


def encoded_string(s: Expr):
    return Concat(Suffix(Itob(Len(s)), Int(6)), s)


T = TypeVar("T", bound=BaseType)


class StringTypeSpec(DynamicArrayTypeSpec):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec())

    def new_instance(self) -> "String":
        return String()

    def __str__(self) -> str:
        return "string"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StringTypeSpec)


StringTypeSpec.__module__ = "pyteal"


class String(DynamicArray):
    def __init__(self) -> None:
        super().__init__(StringTypeSpec())

    def type_spec(self) -> StringTypeSpec:
        return StringTypeSpec()

    def get(self) -> Expr:
        return Suffix(
            self.stored_value.load(), Int(Uint16TypeSpec().byte_length_static())
        )

    def set(
        self,
        value: Union[
            Sequence[T],
            DynamicArray[T],
            ComputedValue[DynamicArray[T]],
            "String",
            str,
            bytes,
            Expr,
        ],
    ) -> Expr:

        # Assume length prefixed
        if isinstance(value, ComputedValue):
            if not isinstance(value.produced_type_spec(), StringTypeSpec):
                raise TealInputError(
                    f"Got ComputedValue with type spec {value.produced_type_spec()}, expected StringTypeSpec"
                )
            return value.store_into(self)

        if isinstance(value, BaseType):
            if isinstance(value.type_spec(), StringTypeSpec):
                return self.decode(value.encode())

            if isinstance(value.type_spec(), DynamicArrayTypeSpec) and isinstance(
                value.type_spec().value_type_spec(), ByteTypeSpec
            ):
                return self.decode(value.encode())

            raise TealInputError(
                f"Got {value} with type spec {value.type_spec()}, expected {StringTypeSpec}"
            )

        # Assume not length prefixed
        if isinstance(value, str) or isinstance(value, bytes):
            return self.stored_value.store(encoded_string(Bytes(value)))

        if isinstance(value, Expr):
            return self.stored_value.store(encoded_string(value))

        if isinstance(value, Sequence):
            return super().set(value)

        raise TealInputError(
            f"Got {value}, expected Sequence, DynamicArray, ComputedValue, String, str, bytes, Expr"
        )


String.__module__ = "pyteal"
