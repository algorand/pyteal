from typing import Union, Sequence, TypeVar, cast

from pyteal.errors import TealInputError
from pyteal.ast.expr import Expr
from pyteal.ast.seq import Seq
from pyteal.ast.int import Int
from pyteal.ast.substring import Suffix

from pyteal.ast.abi.type import ComputedValue, BaseType
from pyteal.ast.abi.uint import Uint16, Byte, ByteTypeSpec
from pyteal.ast.abi.array_base import ArrayTypeSpec, Array


T = TypeVar("T", bound=BaseType)


class DynamicArrayTypeSpec(ArrayTypeSpec[T]):
    def new_instance(self) -> "DynamicArray[T]":
        return DynamicArray(self)

    def annotation_type(self) -> type["DynamicArray[T]"]:
        return DynamicArray[self.value_type_spec().annotation_type()]  # type: ignore[misc]

    def is_length_dynamic(self) -> bool:
        return True

    def is_dynamic(self) -> bool:
        return True

    def byte_length_static(self) -> int:
        raise ValueError("Type is dynamic")

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, DynamicArrayTypeSpec)
            and self.value_type_spec() == other.value_type_spec()
        )

    def __str__(self) -> str:
        return f"{self.value_type_spec()}[]"


DynamicArrayTypeSpec.__module__ = "pyteal.abi"


class DynamicArray(Array[T]):
    """The class that represents ABI dynamic array type."""

    def __init__(self, array_type_spec: DynamicArrayTypeSpec[T]) -> None:
        super().__init__(array_type_spec)

    def type_spec(self) -> DynamicArrayTypeSpec[T]:
        return cast(DynamicArrayTypeSpec[T], super().type_spec())

    def set(
        self,
        values: Union[Sequence[T], "DynamicArray[T]", ComputedValue["DynamicArray[T]"]],
    ) -> Expr:
        """
        Set the elements of this DynamicArray to the input values.

        The behavior of this method depends on the input argument type:

            * :code:`Sequence[T]`: set the elements of this DynamicArray to those contained in this Python sequence (e.g. a list or tuple). A compiler error will occur if any element in the sequence does not match this DynamicArray's element type.
            * :code:`DynamicArray[T]`: copy the elements from another DynamicArray. The argument's element type must exactly match this DynamicArray's element type, otherwise an error will occur.
            * :code:`ComputedValue[DynamicArray[T]]`: copy the elements from a DynamicArray produced by a ComputedValue. The element type produced by the ComputedValue must exactly match this DynamicArray's element type, otherwise an error will occur.

        Args:
            values: The new elements this DynamicArray should have. This must follow the above constraints.

        Returns:
            An expression which stores the given value into this DynamicArray.
        """

        if isinstance(values, ComputedValue):
            return self._set_with_computed_type(values)
        elif isinstance(values, BaseType):
            if self.type_spec() != values.type_spec():
                raise TealInputError(
                    f"Cannot assign type {values.type_spec()} to {self.type_spec()}"
                )
            return self._stored_value.store(values.encode())
        return super().set(values)

    def length(self) -> Expr:
        """Get the element number of this ABI dynamic array.

        The array length (element number) is encoded in the first 2 bytes of the byte encoding.

        Returns:
            A PyTeal expression that represents the dynamic array length.
        """
        output = Uint16()
        return Seq(
            output.decode(self.encode()),
            output.get(),
        )


DynamicArray.__module__ = "pyteal.abi"


class DynamicBytesTypeSpec(DynamicArrayTypeSpec[Byte]):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec())

    def new_instance(self) -> "DynamicBytes":
        return DynamicBytes()

    def annotation_type(self) -> type["DynamicBytes"]:
        return DynamicBytes

    def __str__(self) -> str:
        return "byte[]"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DynamicBytesTypeSpec)


DynamicBytesTypeSpec.__module__ = "pyteal.abi"


class DynamicBytes(DynamicArray[Byte]):
    """The convenience class that represents ABI dynamic byte array."""

    def __init__(self) -> None:
        super().__init__(DynamicBytesTypeSpec())

    def type_spec(self) -> DynamicBytesTypeSpec:
        return DynamicBytesTypeSpec()

    def set(
        self,
        values: Union[
            bytes,
            bytearray,
            Expr,
            Sequence[Byte],
            DynamicArray[Byte],
            ComputedValue[DynamicArray[Byte]],
        ],
    ) -> Expr:
        """Set the elements of this DynamicBytes to the input values.

        The behavior of this method depends on the input argument type:

            * :code:`bytes`: set the value to the Python byte string.
            * :code:`bytearray`: set the value to the Python byte array.
            * :code:`Expr`: set the value to the result of a PyTeal expression, which must evaluate to a TealType.bytes.
            * :code:`Sequence[Byte]`: set the bytes of this String to those contained in this Python sequence (e.g. a list or tuple).
            * :code:`DynamicArray[Byte]`: copy the bytes from another DynamicArray. The argument's element type must exactly match Byte, otherwise an error will occur.
            * :code:`ComputedValue[DynamicArray[Byte]]`: copy the bytes from a DynamicArray produced by a ComputedValue. The argument's element type must exactly match Byte, otherwise an error will occur.

        Args:
            values: The new elements this DynamicBytes should have. This must follow the above constraints.

        Returns:
            An expression which stores the given value into this DynamicBytes.
        """
        # NOTE: the import here is to avoid importing in partial initialized module abi
        from pyteal.ast.abi.string import (
            _encoded_byte_string,
            _store_encoded_expr_byte_string_into_var,
        )

        match values:
            case bytes() | bytearray():
                return self._stored_value.store(_encoded_byte_string(values))
            case Expr():
                return _store_encoded_expr_byte_string_into_var(
                    values, self._stored_value
                )

        return super().set(values)

    def get(self) -> Expr:
        """Get the byte encoding of this DynamicBytes.

        Dropping the uint16 encoding prefix for dynamic array length.

        Returns:
            A Pyteal expression that loads byte encoding of this DynamicBytes, and drop the first uint16 DynamicArray length encoding.
        """
        return Suffix(self._stored_value.load(), Int(2))


DynamicBytes.__module__ = "pyteal.abi"
