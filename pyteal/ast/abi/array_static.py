from typing import (
    Union,
    Sequence,
    TypeVar,
    Generic,
    Final,
    cast,
)

from ...errors import TealInputError
from ..expr import Expr
from ..int import Int

from .type import ComputedType, TypeSpec, BaseType
from .bool import BoolTypeSpec, boolSequenceLength
from .array_base import ArrayTypeSpec, Array, ArrayElement


T = TypeVar("T", bound=BaseType)
N = TypeVar("N", bound=int)


class StaticArrayTypeSpec(ArrayTypeSpec[T], Generic[T, N]):
    def __init__(self, value_type_spec: TypeSpec, array_length: int) -> None:
        super().__init__(value_type_spec)
        if not isinstance(array_length, int) or array_length < 0:
            raise TypeError("Unsupported StaticArray length: {}".format(array_length))
        self.array_length: Final = array_length

    def new_instance(self) -> "StaticArray[T, N]":
        return StaticArray(self.value_type_spec(), self.length_static())

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
        return "{}[{}]".format(self.value_type_spec(), self.length_static())


StaticArrayTypeSpec.__module__ = "pyteal"


class StaticArray(Array[T], Generic[T, N]):
    """The class that represents ABI static array type."""

    def __init__(self, value_type_spec: TypeSpec, array_length: int) -> None:
        super().__init__(StaticArrayTypeSpec(value_type_spec, array_length))

    def type_spec(self) -> StaticArrayTypeSpec[T, N]:
        return cast(StaticArrayTypeSpec[T, N], super().type_spec())

    def set(
        self, values: Union[Sequence[T], "StaticArray[T, N]", ComputedType]
    ) -> Expr:
        """Set the ABI static array with a sequence of ABI type variables, or another ABI static
        array.

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
        if isinstance(values, ComputedType):
            self._set_with_computed_type(values)

        values = cast(Union[Sequence[T], "StaticArray[T, N]"], values)

        if isinstance(values, BaseType):
            if self.type_spec() != values.type_spec():
                raise TealInputError(
                    "Cannot assign type {} to {}".format(
                        values.type_spec(), self.type_spec()
                    )
                )
            return self.stored_value.store(values.encode())

        if self.type_spec().length_static() != len(values):
            raise TealInputError(
                "Incorrect length for values. Expected {}, got {}".format(
                    self.type_spec().length_static(), len(values)
                )
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
            raise TealInputError("Index out of bounds: {}".format(index))
        return super().__getitem__(index)


StaticArray.__module__ = "pyteal"
