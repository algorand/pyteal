from typing import (
    Union,
    Sequence,
    TypeVar,
    cast,
)


from ...errors import TealInputError
from ..expr import Expr
from ..seq import Seq

from .type import TypeSpec, BaseType
from .uint import Uint16
from .array_base import ArrayTypeSpec, Array


T = TypeVar("T", bound=BaseType)


class DynamicArrayTypeSpec(ArrayTypeSpec[T]):
    def new_instance(self) -> "DynamicArray[T]":
        return DynamicArray(self.value_type_spec())

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
        return "{}[]".format(self.value_type_spec())


DynamicArrayTypeSpec.__module__ = "pyteal"


class DynamicArray(Array[T]):
    """The class that represents ABI dynamic array type."""

    def __init__(self, value_type_spec: TypeSpec) -> None:
        super().__init__(DynamicArrayTypeSpec(value_type_spec))

    def get_type_spec(self) -> DynamicArrayTypeSpec[T]:
        return cast(DynamicArrayTypeSpec[T], super().get_type_spec())

    def set(self, values: Union[Sequence[T], "DynamicArray[T]"]) -> Expr:
        """Set the ABI dynamic array with a sequence of ABI type variables, or another ABI dynamic
        array.

        This function determines if the argument `values` is an ABI dynamic array:
        * if so:
          * checks whether `values` is same type as this ABI dynamic array.
          * stores the encoding of `values`.
        * if not:
          * calls the inherited `set` function and stores `values`.

        Args:
            values: either a sequence of ABI typed values, or an ABI dynamic array.

        Returns:
            A PyTeal expression that stores encoded `values` in its internal ScratchVar.
        """
        if isinstance(values, BaseType):
            if self.get_type_spec() != values.get_type_spec():
                raise TealInputError(
                    "Cannot assign type {} to {}".format(
                        values.get_type_spec(), self.get_type_spec()
                    )
                )
            return self.stored_value.store(values.encode())
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


DynamicArray.__module__ = "pyteal"
