from typing import (
    Union,
    Sequence,
    TypeVar,
    cast,
)


from pyteal.errors import TealInputError
from pyteal.ast.expr import Expr
from pyteal.ast.seq import Seq

from pyteal.ast.abi.type import ComputedValue, BaseType
from pyteal.ast.abi.uint import Uint16
from pyteal.ast.abi.array_base import ArrayTypeSpec, Array


T = TypeVar("T", bound=BaseType)


class DynamicArrayTypeSpec(ArrayTypeSpec[T]):
    def new_instance(self) -> "DynamicArray[T]":
        return DynamicArray(self)

    def annotation_type(self) -> "type[DynamicArray[T]]":
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


DynamicArrayTypeSpec.__module__ = "pyteal"


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
        """Set the ABI dynamic array with one of the following
        * a sequence of ABI type variables
        * or another ABI static array
        * or a ComputedType with same TypeSpec

        If the argument `values` is a ComputedType, we call `store_into` method
        from ComputedType to store the internal ABI encoding into this StaticArray.

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

        if isinstance(values, ComputedValue):
            return self._set_with_computed_type(values)
        elif isinstance(values, BaseType):
            if self.type_spec() != values.type_spec():
                raise TealInputError(
                    f"Cannot assign type {values.type_spec()} to {self.type_spec()}"
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
