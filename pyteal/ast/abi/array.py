from typing import (
    Union,
    Sequence,
    TypeVar,
    Generic,
    cast,
    Type as PyType,
    Tuple,
    get_origin,
    get_args,
    Literal,
)
from inspect import isabstract, isclass
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

    @classmethod
    def storage_type(cls) -> TealType:
        return TealType.bytes

    @classmethod
    @abstractmethod
    def value_type(cls) -> PyType[Type]:
        """Get the types of value this array holds."""
        pass

    @classmethod
    @abstractmethod
    def is_length_dynamic(cls) -> bool:
        """Check if this length has a dynamic or static length."""
        pass

    @classmethod
    def _stride(cls) -> int:
        """Get the "stride" of this array.

        The stride is defined as the byte length of each element in the array's encoded "head"
        portion.

        If the underlying value type is static, then the stride is the static byte length of that
        type. Otherwise, the stride is the static byte length of a Uint16 (2 bytes).
        """
        if cls.value_type().is_dynamic():
            return Uint16.byte_length_static()
        return cls.value_type().byte_length_static()

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

        The function first type-check the argument `values` to make sure the sequence of ABI type
        variables before storing them to the underlying ScratchVar. If any of the input element does
        not match expected array element type, error would be raised about type-mismatch.

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
            if not self.value_type().has_same_type_as(value):
                raise TealInputError(
                    "Cannot assign type {} at index {} to {}".format(
                        value, index, self.value_type()
                    )
                )

        encoded = encodeTuple(values)

        if self.is_length_dynamic():
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

        If the argument index is integer, the function will raise an error if the index is negative.

        Args:
            index: either an integer or a PyTeal expression that evaluates to a uint64.

        Returns:
            An ArrayElement that represents the ABI array element at the index.
        """
        if type(index) is int:
            if index < 0:
                raise TealInputError("Index out of bounds: {}".format(index))
            index = Int(index)
        return ArrayElement(self, cast(Expr, index))


Array.__module__ = "pyteal"

N = TypeVar("N", bound=int)


class StaticArray(Array[T], Generic[T, N]):
    """The class that represents ABI static array type."""

    def __class_getitem__(
        cls, params: Tuple[PyType[Type], int]
    ) -> PyType["StaticArray"]:
        assert len(params) == 2
        value_type, length = params

        assert not isabstract(value_type)

        assert issubclass(value_type, Type)
        if get_origin(length) is Literal:
            args = get_args(length)
            assert len(args) == 1
            assert type(args[0]) is int
            length = args[0]

        assert isinstance(length, int)

        if length < 0:
            raise TypeError("Unsupported StaticArray length: {}".format(length))

        class TypedStaticArray(StaticArray):
            def __class_getitem__(cls, _):
                # prevent StaticArray[A, B][C, D]
                raise TypeError("Cannot index into StaticArray[...]")

            @classmethod
            def value_type(cls) -> PyType[Type]:
                return value_type

            @classmethod
            def length_static(cls) -> int:
                return length

        return TypedStaticArray

    @classmethod
    def has_same_type_as(cls, other: Union[PyType[Type], Type]) -> bool:
        """Check if this type is considered equal to the other ABI type, irrespective of their
        values.

        For static array, this is determined by:
        * the equivalence of static array type.
        * the underlying array element type equivalence.
        * the static array length equivalence.

        Args:
            other: The ABI type to compare to.

        Returns:
            True if and only if self and other can store the same ABI value.
        """
        if not isinstance(other, StaticArray) and not (
            isclass(other) and issubclass(other, StaticArray)
        ):
            return False
        return (
            cls.value_type().has_same_type_as(other.value_type())
            and cls.length_static() == other.length_static()
        )

    @classmethod
    def is_dynamic(cls) -> bool:
        """Check if this ABI type is dynamic.

        Whether this ABI static array is dynamic is decided by its array elements' ABI type.
        """
        return cls.value_type().is_dynamic()

    @classmethod
    def byte_length_static(cls) -> int:
        """Get the byte length of this ABI static array's encoding.

        Only valid when array elements' type is static.
        """
        if cls.is_dynamic():
            raise ValueError("Type is dynamic")

        value_type = cls.value_type()
        length = cls.length_static()

        if value_type is Bool:
            return boolSequenceLength(length)
        return length * value_type.byte_length_static()

    @classmethod
    def __str__(cls) -> str:
        """Get the string representation of ABI array type, for creating method signatures."""
        return "{}[{}]".format(cls.value_type().__str__(), cls.length_static())

    @classmethod
    @abstractmethod
    def length_static(cls) -> int:
        """Get the size of this static array type.

        Returns:
            A Python integer that represents the static array length.
        """
        pass

    @classmethod
    def is_length_dynamic(cls) -> bool:
        return False

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
            return self.stored_value.store(values.encode())

        if self.length_static() != len(values):
            raise TealInputError(
                "Incorrect length for values. Expected {}, got {}".format(
                    self.length_static(), len(values)
                )
            )
        return super().set(values)

    def length(self) -> Expr:
        """Get the element number of this ABI static array.

        Returns:
            A PyTeal expression that represents the static array length.
        """
        return Int(self.length_static())

    def __getitem__(self, index: Union[int, Expr]) -> "ArrayElement[T]":
        if type(index) is int and index >= self.length_static():
            raise TealInputError("Index out of bounds: {}".format(index))
        return super().__getitem__(index)


StaticArray.__module__ = "pyteal"


class DynamicArray(Array[T]):
    """The class that represents ABI dynamic array type."""

    def __class_getitem__(cls, value_type: PyType[Type]) -> PyType["DynamicArray"]:
        assert issubclass(value_type, Type)

        assert not isabstract(value_type)

        class TypedDynamicArray(DynamicArray):
            def __class_getitem__(cls, _):
                # prevent DynamicArray[A][B]
                raise TypeError("Cannot index into DynamicArray[...]")

            @classmethod
            def value_type(cls) -> PyType[Type]:
                return value_type

        return TypedDynamicArray

    @classmethod
    def has_same_type_as(cls, other: Union[PyType[Type], Type]) -> bool:
        """Check if this type is considered equal to the other ABI type, irrespective of their
        values.

        For dynamic array, this is determined by
        * the equivalence of dynamic array type.
        * the underlying array element type equivalence.

        Args:
            other: The ABI type to compare to.

        Returns:
            True if and only if self and other can store the same ABI value.
        """
        if not (isclass(other) and issubclass(other, DynamicArray)) and not isinstance(
            other, DynamicArray
        ):
            return False
        return cls.value_type().has_same_type_as(other.value_type())

    @classmethod
    def is_dynamic(cls) -> bool:
        """Check if this ABI type is dynamic.

        An ABI dynamic array is always dynamic.
        """
        return True

    @classmethod
    def byte_length_static(cls) -> int:
        """Get the byte length of this ABI dynamic array's encoding.

        Always raise error for this method is only valid for static ABI types.
        """
        raise ValueError("Type is dynamic")

    @classmethod
    def __str__(cls) -> str:
        """Get the string representation of ABI array type, for creating method signatures."""
        return "{}[]".format(cls.value_type().__str__())

    @classmethod
    def is_length_dynamic(cls) -> bool:
        return True

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
        super().__init__()
        require_type(index, TealType.uint64)
        self.array = array
        self.index = index

    def produced_type(self) -> PyType[T]:
        return self.array.value_type()

    def store_into(self, output: T) -> Expr:
        """Partitions the byte string of the given ABI array and stores the byte string of array
        element in the ABI value output.

        The function first checks if the output type matches with array element type, and throw
        error if type-mismatch.

        Args:
            output: An ABI typed value that the array element byte string stores into.

        Returns:
            An expression that stores the byte string of the array element into value `output`.
        """
        if not self.array.value_type().has_same_type_as(output) or not isinstance(
            output, Type
        ):
            raise TealInputError("Output type does not match value type")

        encodedArray = self.array.encode()

        # If the array element type is Bool, we compute the bit index
        # (if array is dynamic we add 16 to bit index for dynamic array length uint16 prefix)
        # and decode bit with given array encoding and the bit index for boolean bit.
        if type(output) is Bool:
            bitIndex = self.index
            if self.array.is_dynamic():
                bitIndex = bitIndex + Int(Uint16.bit_size())
            return cast(Bool, output).decodeBit(encodedArray, bitIndex)

        # Compute the byteIndex (first byte indicating the element encoding)
        # (If the array is dynamic, add 2 to byte index for dynamic array length uint16 prefix)
        byteIndex = Int(self.array._stride()) * self.index
        if self.array.is_length_dynamic():
            byteIndex = byteIndex + Int(Uint16.byte_length_static())

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
        if self.array.value_type().is_dynamic():
            valueStart = ExtractUint16(encodedArray, byteIndex)
            nextValueStart = ExtractUint16(
                encodedArray, byteIndex + Int(Uint16.byte_length_static())
            )
            if self.array.is_length_dynamic():
                valueStart = valueStart + Int(Uint16.byte_length_static())
                nextValueStart = nextValueStart + Int(Uint16.byte_length_static())

            valueEnd = (
                If(self.index + Int(1) == arrayLength)
                .Then(Len(encodedArray))
                .Else(nextValueStart)
            )

            return output.decode(encodedArray, startIndex=valueStart, endIndex=valueEnd)

        # Handling case for array elements are static:
        # since array._stride() is element's static byte length
        # we partition the substring for array element.
        valueStart = byteIndex
        valueLength = Int(self.array._stride())
        return output.decode(encodedArray, startIndex=valueStart, length=valueLength)


ArrayElement.__module__ = "pyteal"
