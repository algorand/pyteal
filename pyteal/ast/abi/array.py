from typing import (
    Union,
    Sequence,
    TypeVar,
    Generic,
    Optional,
    cast,
)
from abc import abstractmethod

from ...types import TealType, require_type
from ...errors import TealInputError
from ..expr import Expr
from ..seq import Seq
from ..int import Int
from ..if_ import If
from ..unaryexpr import Len
from ..binaryexpr import ExtractUint16
from ..naryexpr import Concat

from .type import Type, ComputedType, substringForDecoding
from .tuple import encodeTuple
from .bool import Bool, boolSequenceLength
from .uint import Uint16


T = TypeVar("T", bound=Type)


class Array(Type, Generic[T]):
    """The base class for both ABI static array and ABI dynamic array.

    This class contains
    * both underlying array element ABI type and an optional array length
    * a basic implementation for inherited ABI static and dynamic array types, including
      * basic array elements setting method
      * string representation for ABI array
      * basic encoding and decoding of ABI array
      * item retrieving by index (expression or integer)
    """

    def __init__(self, valueType: T, staticLength: Optional[int]) -> None:
        """Creates a new ABI array.

        This function determines distinct storage format over byte string by inferring if the array
        element type is static:
        * if it is static, then the stride is the static byte length of the element.
        * otherwise the stride is 2 bytes, which is the size of a Uint16.

        This function also stores the static array length of an instance of ABI array, if it exists.

        Args:
            valueType: The ABI type of the array element.
            staticLength (optional): An integer representing the static length of the array.
        """
        super().__init__(TealType.bytes)
        self._valueType = valueType

        self._has_offsets = valueType.is_dynamic()
        if self._has_offsets:
            self._stride = Uint16().byte_length_static()
        else:
            self._stride = valueType.byte_length_static()
        self._static_length = staticLength

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        """Decode a substring of the passed in encoded byte string and set it as this type's value.

        Args:
            encoded: An expression containing the bytes to decode. Must evaluate to TealType.bytes.
            startIndex (optional): An expression containing the index to start decoding. Must
                evaluate to TealType.uint64. Defaults to None.
            endIndex (optional): An expression containing the index to stop decoding. Must evaluate
                to TealType.uint64. Defaults to None.
            length (optional): An expression containing the length of the substring to decode. Must
                evaluate to TealType.uint64. Defaults to None.

        Returns:
            An expression that partitions the needed parts from given byte strings and stores into
            the scratch variable.
        """
        extracted = substringForDecoding(
            encoded, startIndex=startIndex, endIndex=endIndex, length=length
        )
        return self.stored_value.store(extracted)

    def set(self, values: Sequence[T]) -> Expr:
        """Set the ABI array with a sequence of ABI type variables.

        The argument to this function is meant to be type-checked before storing to the underlying
        ScratchVar. If any of the input sequence element does not match expected array element type,
        error would be raised about type-unmatch.

        If static length of array is not available, this function would
        * infer the array length from the sequence element number.
        * store the inferred array length in uint16 format.
        * concatenate the encoded array length at the beginning of array encoding.

        Args:
            values: The sequence of ABI type variables to store in ABI array.

        Returns:
            A PyTeal expression that stores encoded sequence of ABI values in its internal
            ScratchVar.
        """
        for index, value in enumerate(values):
            if not self._valueType.has_same_type_as(value):
                raise TealInputError(
                    "Cannot assign type {} at index {} to {}".format(
                        value, index, self._valueType
                    )
                )

        encoded = encodeTuple(values)

        if self._static_length is None:
            length_tmp = Uint16()
            length_prefix = Seq(length_tmp.set(len(values)), length_tmp.encode())
            encoded = Concat(length_prefix, encoded)

        return self.stored_value.store(encoded)

    def encode(self) -> Expr:
        """Encode the ABI array to be a byte string.

        Returns:
            A PyTeal expression that encodes this ABI array to a byte string.
        """
        return self.stored_value.load()

    @abstractmethod
    def length(self) -> Expr:
        """Get the element number of this ABI array.

        Returns:
            A PyTeal expression that represents the array length.
        """
        pass

    def __getitem__(self, index: Union[int, Expr]) -> "ArrayElement[T]":
        """Retrieve an ABI array element by an index (either a PyTeal expression or an integer).

        If the static array length is available and the argument index is integer, the function
        checks if the index is in [0, static_length - 1].

        Args:
            index: either an integer or a PyTeal expression that evaluates to a uint64.

        Returns:
            An ArrayElement that represents the ABI array element at the index.
        """
        if type(index) is int:
            if index < 0 or (
                self._static_length is not None and index >= self._static_length
            ):
                raise TealInputError("Index out of bounds: {}".format(index))
            index = Int(index)
        return ArrayElement(self, cast(Expr, index))

    def __str__(self) -> str:
        """Get the string representation of ABI array type, for creating method signatures."""
        return self._valueType.__str__() + (
            "[]" if self._static_length is None else "[{}]".format(self._static_length)
        )


Array.__module__ = "pyteal"

# until something like https://github.com/python/mypy/issues/3345 is added, we can't make the size of the array a generic parameter
class StaticArray(Array[T]):
    """The class that represents ABI static array type.

    This class requires static length on initialization.
    """

    def __init__(self, valueType: T, length: int) -> None:
        """Create a new static array.

        Checks if the static array length is non-negative, if it is negative throw error.

        Args:
            valueType: The ABI type of the array element.
            length: An integer representing the static length of the array.
        """
        if length < 0:
            raise TealInputError(
                "Static array length cannot be negative. Got {}".format(length)
            )
        super().__init__(valueType, length)

    def has_same_type_as(self, other: Type) -> bool:
        """Check if this type is considered equal to the other ABI type, irrespective of their
        values.

        For static array, this is determined by:
        * the equivalance of static array type.
        * the underlying array element type equivalance.
        * the static array length equivalance.

        Args:
            other: The ABI type to compare to.

        Returns:
            True if and only if self and other can store the same ABI value.
        """
        return (
            type(other) is StaticArray
            and self._valueType.has_same_type_as(other._valueType)
            and self.length_static() == other.length_static()
        )

    def new_instance(self) -> "StaticArray[T]":
        """Create a new instance of this ABI type.

        The value of this type will not be applied to the new type.
        """
        return StaticArray(self._valueType, self.length_static())

    def is_dynamic(self) -> bool:
        """Check if this ABI type is dynamic.

        Whether this ABI static array is dymamic is decided by its array elements' ABI type.
        """
        return self._valueType.is_dynamic()

    def byte_length_static(self) -> int:
        """Get the byte length of this ABI static array's encoding.

        Only valid when array elements' type is static.
        """
        if self.is_dynamic():
            raise ValueError("Type is dynamic")
        if type(self._valueType) is Bool:
            return boolSequenceLength(self.length_static())
        return self.length_static() * self._valueType.byte_length_static()

    def set(self, values: Union[Sequence[T], "StaticArray[T]"]) -> Expr:
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
        if isinstance(values, Type):
            if not self.has_same_type_as(values):
                raise TealInputError("Cannot assign type {} to {}".format(values, self))
            return self.stored_value.store(cast(StaticArray[T], values).encode())

        if self.length_static() != len(values):
            raise TealInputError(
                "Incorrect length for values. Expected {}, got {}".format(
                    self.length_static(), len(values)
                )
            )
        return super().set(values)

    def length_static(self) -> int:
        """Get the element number of this static ABI array.

        Returns:
            A Python integer that represents the static array length.
        """
        return cast(int, self._static_length)

    def length(self) -> Expr:
        """Get the element number of this ABI static array.

        Returns:
            A PyTeal expression that represents the static array length.
        """
        return Int(self.length_static())


StaticArray.__module__ = "pyteal"


class DynamicArray(Array[T]):
    """The class that represents ABI dynamic array type."""

    def __init__(self, valueType: T) -> None:
        """Creates a new dynamic array.

        Args:
            valueType: The ABI type of the array element.
        """
        super().__init__(valueType, None)

    def has_same_type_as(self, other: Type) -> bool:
        """Check if this type is considered equal to the other ABI type, irrespective of their
        values.

        For dynamic array, this is determined by
        * the equivalance of dynamic array type.
        * the underlying array element type equivalence.

        Args:
            other: The ABI type to compare to.

        Returns:
            True if and only if self and other can store the same ABI value.
        """
        return type(other) is DynamicArray and self._valueType.has_same_type_as(
            other._valueType
        )

    def new_instance(self) -> "DynamicArray[T]":
        """Create a new instance of this ABI type.

        The value of this type will not be applied to the new type.
        """
        return DynamicArray(self._valueType)

    def is_dynamic(self) -> bool:
        """Check if this ABI type is dynamic.

        An ABI dynamic array is always dynamic.
        """
        return True

    def byte_length_static(self) -> int:
        """Get the byte length of this ABI dynamic array's encoding.

        Always raise error for this method is only valid for static ABI types.
        """
        raise ValueError("Type is dynamic")

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
        if isinstance(values, Type):
            if not self.has_same_type_as(values):
                raise TealInputError("Cannot assign type {} to {}".format(values, self))
            return self.stored_value.store(cast(DynamicArray[T], values).encode())
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


class ArrayElement(ComputedType[T]):
    """The class that represents an ABI array element.

    This class requires a reference to the array that the array element belongs to, and a PyTeal
    expression (required to be TealType.uint64) which stands for array index.
    """

    def __init__(self, array: Array[T], index: Expr) -> None:
        """Creates a new ArrayElement.

        Args:
            array: The ABI array that the array element belongs to.
            index: A PyTeal expression (required to be TealType.uint64) stands for array index.
        """
        super().__init__(array._valueType)
        require_type(index, TealType.uint64)
        self.array = array
        self.index = index

    def store_into(self, output: T) -> Expr:
        """Partitions the byte string of the given ABI array and stores the byte string of array
        element in the ABI value output.

        The function first checks if the output type matches with array element type, and throw
        error if type-unmatch.

        Args:
            output: An ABI typed value that the array element byte string stores into.

        Returns:
            An expression that stores the byte string of the array element into value `output`.
        """
        if not self.array._valueType.has_same_type_as(output):
            raise TealInputError("Output type does not match value type")

        encodedArray = self.array.encode()

        # If the array element type is Bool, we compute the bit index
        # (if array is dynamic we add 16 to bit index for dynamic array length uint16 prefix)
        # and decode bit with given array encoding and the bit index for boolean bit.
        if type(output) is Bool:
            bitIndex = self.index
            if self.array.is_dynamic():
                bitIndex = bitIndex + Int(Uint16().bits())
            return cast(Bool, output).decodeBit(encodedArray, bitIndex)

        # Compute the byteIndex (first byte indicating the element encoding)
        # (If the array is dynamic, add 2 to byte index for dynamic array length uint16 prefix)
        byteIndex = Int(self.array._stride) * self.index
        if self.array._static_length is None:
            byteIndex = byteIndex + Int(Uint16().byte_length_static())

        arrayLength = self.array.length()

        # Handling case for array elements are dynamic:
        # * `byteIndex` is pointing at the uint16 byte encoding indicating the beginning offset of
        #   the array element byte encoding.
        #
        # * `valueStart` is extracted from the uint16 bytes pointed by `byteIndex`.
        #
        # * If `index == arrayLength - 1` (last element in array), `valueEnd` is pointing at the
        #   end of the array byte encoding.
        #
        # * otherwise, `valueEnd` is inferred from `nextValueStart`, which is the beginning offset
        #   of the next array element byte encoding.
        if self.array._valueType.is_dynamic():
            valueStart = ExtractUint16(encodedArray, byteIndex)
            nextValueStart = ExtractUint16(
                encodedArray, byteIndex + Int(Uint16().byte_length_static())
            )
            if self.array._static_length is None:
                valueStart = valueStart + Int(Uint16().byte_length_static())
                nextValueStart = nextValueStart + Int(Uint16().byte_length_static())

            valueEnd = (
                If(self.index + Int(1) == arrayLength)
                .Then(Len(encodedArray))
                .Else(nextValueStart)
            )

            return output.decode(encodedArray, startIndex=valueStart, endIndex=valueEnd)

        # Handling case for array elements are static:
        # since array._stride is element's static byte length
        # we partition the substring for array element.
        valueStart = byteIndex
        valueLength = Int(self.array._stride)
        return output.decode(encodedArray, startIndex=valueStart, length=valueLength)


ArrayElement.__module__ = "pyteal"
