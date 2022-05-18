from typing import Final, Generic, Literal, Sequence, TypeVar, Union, cast

from pyteal.errors import TealInputError
from pyteal.ast.expr import Expr
from pyteal.ast.int import Int

from pyteal.ast.abi.type import ComputedValue, TypeSpec, BaseType
from pyteal.ast.abi.bool import BoolTypeSpec, boolSequenceLength
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

    def annotation_type(self) -> "type[StaticArray[T, N]]":
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
            return boolSequenceLength(length)
        return length * value_type.byte_length_static()

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, StaticArrayTypeSpec)
            and self.value_type_spec() == other.value_type_spec()
            and self.length_static() == other.length_static()
        )

    def __str__(self) -> str:
        return f"{self.value_type_spec()}[{self.length_static()}]"


StaticArrayTypeSpec.__module__ = "pyteal"


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
        """Set the ABI static array with one of the following:
        * a sequence of ABI type variables
        * or another ABI static array
        * or a ComputedType with same TypeSpec

        If the argument `values` is a ComputedType, we call `store_into` method
        from ComputedType to store the internal ABI encoding into this StaticArray.

        This function determines if the argument `values` is an ABI static array:
        * if so:
          * checks whether `values` is same type as this ABI staic array.
          * stores the encoding of `values`.
        * if not:
          * checks whether static array length matches sequence length.
          * calls the inherited `set` function and stores `values`.

        Args:
            values: either a sequence of ABI typed values, or an ABI static array.

        Returns:
            A PyTeal expression that stores encoded `values` in its internal ScratchVar.
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
        if type(index) is int and index >= self.type_spec().length_static():
            raise TealInputError(f"Index out of bounds: {index}")
        return super().__getitem__(index)


StaticArray.__module__ = "pyteal"
