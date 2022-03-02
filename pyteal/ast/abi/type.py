from typing import TypeVar, Generic, Callable, Type as PyType, Union
from abc import ABC, abstractmethod

from ...types import TealType
from ...errors import TealInputError
from ..expr import Expr
from ..scratchvar import ScratchVar
from ..seq import Seq
from ..int import Int
from ..substring import Extract, Substring, Suffix


class Type(ABC):
    """The abstract base class for all ABI types.

    This class contains both information about an ABI type, and a value that conforms to that type.
    The value is contained in a unique ScratchVar that only the type has access to. As a result, the
    value of an ABI type is mutable and can be efficiently referenced multiple times without needing
    to recompute it.
    """

    def __init__(self) -> None:
        """Create a new Type.

        Every subclass of Type must allow its __init__ method to be called with no arguments.
        """
        super().__init__()
        self.stored_value = ScratchVar(self.storage_type())

    @classmethod
    @abstractmethod
    def has_same_type_as(cls, other: Union[PyType["Type"], "Type"]) -> bool:
        """Check if this type is considered equal to the other ABI type, irrespective of the values
        of types.

        Args:
            other: The ABI type to compare to. This may be an instance of Type or a subclass of Type.

        Returns:
            True if and only if self and other conform to the same ABI type.
        """
        pass

    @classmethod
    @abstractmethod
    def is_dynamic(cls) -> bool:
        """Check if this ABI type is dynamic.

        If a type is dynamic, the length of its encoding depends on its value. Otherwise, the type
        is considered static (not dynamic).
        """
        pass

    @classmethod
    @abstractmethod
    def byte_length_static(cls) -> int:
        """Get the byte length of this ABI type's encoding. Only valid for static types."""
        pass

    @classmethod
    @abstractmethod
    def storage_type(cls) -> TealType:
        """Get the TealType that the underlying ScratchVar should hold for this type."""
        pass

    @classmethod
    @abstractmethod
    def __str__(cls) -> str:
        """Get the string representation of this ABI type, used for creating method signatures."""
        pass

    @abstractmethod
    def encode(self) -> Expr:
        """Encode this ABI type to a byte string.

        Returns:
            A PyTeal expression that encodes this type to a byte string.
        """
        pass

    @abstractmethod
    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        """Decode a substring of the passed in encoded string and set it as this type's value.

        The arguments to this function are means to be as flexible as possible for the caller.
        Multiple types of substrings can be specified based on the arguments, as listed below:

        * Entire string: if startIndex, endIndex, and length are all None, the entire encoded string
          is decoded.
        * Prefix: if startIndex is None and one of endIndex or length is provided, a prefix of the
          encoded string is decoded. The range is 0 through endIndex or length (they are equivalent).
        * Suffix: if startIndex is provided and endIndex and length are None, a suffix of the encoded
          string is decoded. The range is startIndex through the end of the string.
        * Substring specified with endIndex: if startIndex and endIndex are provided and length is
          None, a substring of the encoded string is decoded. The range is startIndex through
          endIndex.
        * Substring specified with length: if startIndex and length are provided and endIndex is
          None, a substring of the encoded string is decoded. The range is startIndex through
          startIndex+length.

        Args:
            encoded: An expression containing the bytes to decode. Must evaluate to TealType.bytes.
            startIndex (optional): An expression containing the index to start decoding. Must
                evaluate to TealType.uint64. Defaults to None.
            endIndex (optional): An expression containing the index to stop decoding. Must evaluate
                to TealType.uint64. Defaults to None.
            length (optional): An expression containing the length of the substring to decode. Must
                evaluate to TealType.uint64. Defaults to None.

        Returns:
            An expression that performs the necessary steps in order to decode the given string into
            a value.
        """
        pass


Type.__module__ = "pyteal"

T = TypeVar("T", bound=Type)


class ComputedType(ABC, Generic[T]):
    """Represents an ABI Type whose value must be computed by an expression."""

    @abstractmethod
    def produced_type(cls) -> PyType[T]:
        """Get the ABI Type that this object produces.

        Returns:
            The type class of the produced ABI type. This class should be immediately instantiable
            with no arguments.
        """
        pass

    @abstractmethod
    def store_into(self, output: T) -> Expr:
        """Store the value of this computed type into an existing ABI Type object.

        Args:
            output: The object where the computed value will be stored. This object must have the
                same type as this class's produced type.

        Returns:
            An expression which stores the computed value represented by this class into the output
            object.
        """
        pass

    def use(self, action: Callable[[T], Expr]) -> Expr:
        """Use the computed value represented by this class in a function or lambda expression.

        Args:
            action: A callable object that will receive an instance of this class's produced type
                with the correct value. TODO: explanation of the callable's return value

        Returns:
            TODO
        """
        newInstance = self.produced_type()()
        return Seq(self.store_into(newInstance), action(newInstance))


ComputedType.__module__ = "pyteal"


def substringForDecoding(
    encoded: Expr,
    *,
    startIndex: Expr = None,
    endIndex: Expr = None,
    length: Expr = None
) -> Expr:
    """A helper function for getting the substring to decode according to the rules of Type.decode."""
    if length is not None and endIndex is not None:
        raise TealInputError("length and endIndex are mutually exclusive arguments")

    if startIndex is not None:
        if length is not None:
            # substring from startIndex to startIndex + length
            return Extract(encoded, startIndex, length)

        if endIndex is not None:
            # substring from startIndex to endIndex
            return Substring(encoded, startIndex, endIndex)

        # substring from startIndex to end of string
        return Suffix(encoded, startIndex)

    if length is not None:
        # substring from 0 to length
        return Extract(encoded, Int(0), length)

    if endIndex is not None:
        # substring from 0 to endIndex
        return Substring(encoded, Int(0), endIndex)

    # the entire string
    return encoded
