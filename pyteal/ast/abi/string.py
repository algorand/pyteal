from typing import Union, Sequence, cast
from collections.abc import Sequence as CollectionSequence

from algosdk.abi import ABIType

from pyteal.ast.abi.uint import Byte
from pyteal.ast.abi.type import ComputedValue, BaseType
from pyteal.ast.abi.array_dynamic import DynamicArray, DynamicArrayTypeSpec
from pyteal.ast.abi.uint import ByteTypeSpec, Uint16TypeSpec

from pyteal.ast.int import Int
from pyteal.ast.expr import Expr
from pyteal.ast.bytes import Bytes
from pyteal.ast.seq import Seq
from pyteal.ast.scratchvar import ScratchVar
from pyteal.ast.unaryexpr import Itob, Len
from pyteal.ast.substring import Suffix
from pyteal.ast.naryexpr import Concat

from pyteal.errors import TealInputError


def _encoded_byte_string(s: bytes | bytearray) -> Expr:
    prefix = ABIType.from_string("uint16").encode(len(s))
    return Bytes(prefix + s)


def _store_encoded_expr_byte_string_into_var(value: Expr, location: ScratchVar) -> Expr:
    return Seq(
        location.store(value),
        location.store(
            Concat(Suffix(Itob(Len(location.load())), Int(6)), location.load())
        ),
    )


class StringTypeSpec(DynamicArrayTypeSpec):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec())

    def new_instance(self) -> "String":
        return String()

    def annotation_type(self) -> "type[String]":
        return String

    def __str__(self) -> str:
        return "string"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StringTypeSpec)


StringTypeSpec.__module__ = "pyteal.abi"


class String(DynamicArray[Byte]):
    def __init__(self) -> None:
        super().__init__(StringTypeSpec())

    def type_spec(self) -> StringTypeSpec:
        return StringTypeSpec()

    def get(self) -> Expr:
        """Return the value held by this String as a PyTeal expression.

        The expression will have the type TealType.bytes.
        """
        return Suffix(
            self.stored_value.load(), Int(Uint16TypeSpec().byte_length_static())
        )

    def set(
        self,
        value: Union[
            str,
            bytes,
            Expr,
            Sequence[Byte],
            DynamicArray[Byte],
            ComputedValue[DynamicArray[Byte]],
            "String",
            ComputedValue["String"],
        ],
    ) -> Expr:
        """Set the value of this String to the input value.

        The behavior of this method depends on the input argument type:

            * :code:`str`: set the value to the Python string.
            * :code:`bytes`: set the value to the Python byte string.
            * :code:`Expr`: set the value to the result of a PyTeal expression, which must evaluate to a TealType.bytes.
            * :code:`Sequence[Byte]`: set the bytes of this String to those contained in this Python sequence (e.g. a list or tuple).
            * :code:`DynamicArray[Byte]`: copy the bytes from a DynamicArray.
            * :code:`ComputedValue[DynamicArray[Byte]]`: copy the bytes from a DynamicArray produced by a ComputedValue.
            * :code:`String`: copy the value from another String.
            * :code:`ComputedValue[String]`: copy the value from a String produced by a ComputedValue.

        Args:
            value: The new value this String should take. This must follow the above constraints.

        Returns:
            An expression which stores the given value into this String.
        """

        match value:
            case ComputedValue():
                return self._set_with_computed_type(value)
            case BaseType():
                if value.type_spec() == StringTypeSpec() or (
                    value.type_spec() == DynamicArrayTypeSpec(ByteTypeSpec())
                ):
                    return self.stored_value.store(value.stored_value.load())

                raise TealInputError(
                    f"Got {value} with type spec {value.type_spec()}, expected {StringTypeSpec}"
                )
            case bytes() | bytearray():
                return self.stored_value.store(_encoded_byte_string(value))
            case str():
                return self.stored_value.store(_encoded_byte_string(value.encode()))
            case Expr():
                return _store_encoded_expr_byte_string_into_var(
                    value, self.stored_value
                )
            case CollectionSequence():
                return super().set(cast(Sequence[Byte], value))

        raise TealInputError(
            f"Got {type(value)}, expected DynamicArray, ComputedValue, String, str, bytes, Expr"
        )


String.__module__ = "pyteal.abi"
