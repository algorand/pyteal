from typing import Final, Generic, Literal, Sequence, TypeVar, Union, cast

from pyteal.errors import TealInputError
from pyteal.ast.assert_ import Assert
from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from pyteal.ast.bytes import Bytes
from pyteal.ast.seq import Seq
from pyteal.ast.unaryexpr import Len

from pyteal.ast.abi.type import ComputedValue, TypeSpec, BaseType
from pyteal.ast.abi.bool import BoolTypeSpec, _bool_sequence_length
from pyteal.ast.abi.uint import Byte, ByteTypeSpec
from pyteal.ast.abi.array_base import ArrayTypeSpec, Array, ArrayElement

T = TypeVar("T", bound=BaseType)
N = TypeVar("N", bound=int)


class StaticArrayTypeSpec(ArrayTypeSpec[T], Generic[T, N]):
    def __init__(self, value_type_spec: TypeSpec, array_length: int) -> None:
        super().__init__(value_type_spec)
        if not isinstance(array_length, int) or array_length < 0:
            raise TypeError(f"Unsupported StaticArray length: {array_length}")

        # Casts to `int` to handle downstream usage where value is a subclass of int like `IntEnum`.
        self.array_length: Final = int(array_length)

    def new_instance(self) -> "StaticArray[T, N]":
        return StaticArray(self)

    def annotation_type(self) -> type["StaticArray[T, N]"]:
        return StaticArray[  # type: ignore[misc]
            self.value_spec.annotation_type(), Literal[self.array_length]  # type: ignore
        ]

    def length_static(self) -> int:
        """Get the size of this static array type.

        Returns:
            A Python integer that represents the static array length.
        """
        return self.array_length

    def is_length_dynamic(self) -> bool:
        return False

    def is_dynamic(self) -> bool:
        return self.value_type_spec().is_dynamic()

    def byte_length_static(self) -> int:
        if self.is_dynamic():
            raise ValueError("Type is dynamic")

        value_type = self.value_type_spec()
        length = self.length_static()

        if value_type == BoolTypeSpec():
            return _bool_sequence_length(length)
        return length * value_type.byte_length_static()

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, StaticArrayTypeSpec)
            and self.value_type_spec() == other.value_type_spec()
            and self.length_static() == other.length_static()
        )

    def __str__(self) -> str:
        return f"{self.value_type_spec()}[{self.length_static()}]"


StaticArrayTypeSpec.__module__ = "pyteal.abi"


class StaticArray(Array[T], Generic[T, N]):
    """The class that represents ABI static array type."""

    def __init__(self, array_type_spec: StaticArrayTypeSpec[T, N]) -> None:
        super().__init__(array_type_spec)

    def type_spec(self) -> StaticArrayTypeSpec[T, N]:
        return cast(StaticArrayTypeSpec[T, N], super().type_spec())

    def set(
        self,
        values: Union[
            Sequence[T], "StaticArray[T, N]", ComputedValue["StaticArray[T, N]"]
        ],
    ) -> Expr:
        """Set the elements of this StaticArray to the input values.

        The behavior of this method depends on the input argument type:

            * :code:`Sequence[T]`: set the elements of this StaticArray to those contained in this Python sequence (e.g. a list or tuple). A compiler error will occur if any element in the sequence does not match this StaticArray's element type, or if the sequence length does not equal this StaticArray's length.
            * :code:`StaticArray[T, N]`: copy the elements from another StaticArray. The argument's element type and length must exactly match this StaticArray's element type and length, otherwise an error will occur.
            * :code:`ComputedValue[StaticArray[T, N]]`: copy the elements from a StaticArray produced by a ComputedValue. The element type and length produced by the ComputedValue must exactly match this StaticArray's element type and length, otherwise an error will occur.

        Args:
            values: The new elements this StaticArray should have. This must follow the above constraints.

        Returns:
            An expression which stores the given value into this StaticArray.
        """
        if isinstance(values, ComputedValue):
            return self._set_with_computed_type(values)
        elif isinstance(values, BaseType):
            if self.type_spec() != values.type_spec():
                raise TealInputError(
                    f"Cannot assign type {values.type_spec()} to {self.type_spec()}"
                )
            return self.stored_value.store(values.encode())

        if self.type_spec().length_static() != len(values):
            raise TealInputError(
                f"Incorrect length for values. Expected {self.type_spec()}, got {len(values)}"
            )
        return super().set(values)

    def length(self) -> Expr:
        """Get the element number of this ABI static array.

        Returns:
            A PyTeal expression that represents the static array length.
        """
        return Int(self.type_spec().length_static())

    def __getitem__(self, index: Union[int, Expr]) -> "ArrayElement[T]":
        """Retrieve an element by its index in this StaticArray.

        Indexes start at 0.

        Args:
            index: either a Python integer or a PyTeal expression that evaluates to a TealType.uint64.
                If a Python integer is used, this function will raise an error if its value is negative
                or if the index is equal to or greater than the length of this StaticArray. If a PyTeal
                expression is used, the program will fail at runtime if the index is outside of the
                bounds of this StaticArray.

        Returns:
            An ArrayElement that corresponds to the element at the given index. This type is a ComputedValue.
        """
        if type(index) is int and index >= self.type_spec().length_static():
            raise TealInputError(f"Index out of bounds: {index}")
        return super().__getitem__(index)


StaticArray.__module__ = "pyteal.abi"


class StaticBytesTypeSpec(StaticArrayTypeSpec[Byte, N], Generic[N]):
    def __init__(self, array_length: int) -> None:
        super().__init__(ByteTypeSpec(), array_length)

    def new_instance(self) -> "StaticBytes[N]":
        return StaticBytes(self)

    def annotation_type(self) -> type["StaticBytes[N]"]:
        return StaticBytes[  # type: ignore[misc]
            Literal[self.array_length]  # type: ignore
        ]


StaticBytesTypeSpec.__module__ = "pyteal.abi"


class StaticBytes(StaticArray[Byte, N], Generic[N]):
    """The convenience class that represents ABI static byte array."""

    def __init__(self, array_type_spec: StaticBytesTypeSpec[N]) -> None:
        super().__init__(array_type_spec)

    def type_spec(self) -> StaticBytesTypeSpec:
        return cast(StaticBytesTypeSpec[N], super().type_spec())

    def set(
        self,
        values: Union[
            bytes,
            bytearray,
            Expr,
            Sequence[Byte],
            StaticArray[Byte, N],
            ComputedValue[StaticArray[Byte, N]],
        ],
    ) -> Expr:
        """Set the elements of this StaticBytes to the input values.

        The behavior of this method depends on the input argument type:

            * :code:`bytes`: set the value to the Python byte string.
            * :code:`bytearray`: set the value to the Python byte array.
            * :code:`Expr`: set the value to the result of a PyTeal expression, which must evaluate to a TealType.bytes.
            * :code:`Sequence[Byte]`: set the bytes of this String to those contained in this Python sequence (e.g. a list or tuple).
            * :code:`StaticArray[Byte, N]`: copy the bytes from another StaticArray. The argument's element type and length must exactly match Byte and this StaticBytes' length, otherwise an error will occur.
            * :code:`ComputedValue[StaticArray[Byte, N]]`: copy the bytes from a StaticArray produced by a ComputedType. The argument's element type and length must exactly match Byte and this StaticBytes' length, otherwise an error will occur.

        Args:
            values: The new elements this StaticBytes should have. This must follow the above constraints.

        Returns:
            An expression which stores the given value into this StaticBytes.
        """
        match values:
            case bytes() | bytearray():
                if len(values) != self.type_spec().length_static():
                    raise TealInputError(
                        f"Got bytes with length {len(values)}, expect {self.type_spec().length_static()}"
                    )
                return self.stored_value.store(Bytes(values))
            case Expr():
                return Seq(
                    self.stored_value.store(values),
                    Assert(self.length() == Len(self.stored_value.load())),
                )

        return super().set(values)

    def get(self) -> Expr:
        """Get the byte encoding of this StaticBytes.

        Returns:
            A Pyteal expression that loads byte encoding of this StaticBytes.
        """
        return self.stored_value.load()


StaticBytes.__module__ = "pyteal.abi"
