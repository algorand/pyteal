from typing import TypeVar, Generic, Callable
from abc import ABC, abstractmethod

from ...types import TealType
from ...errors import TealInputError
from ..expr import Expr
from ..scratchvar import ScratchVar
from ..seq import Seq
from ..int import Int
from ..substring import Extract, Substring, Suffix

T = TypeVar("T", bound="Type")


class Type(ABC):
    """The abstract base class for all ABI types.
    
    This class contains both information about an ABI type, and a value that conforms to that type.
    The value is contained in a unique ScratchVar that only the type has access to. As a result, the
    value of an ABI type is mutable and can be efficiently referenced multiple times without needing
    to recompute it.
    """

    def __init__(self, valueType: TealType) -> None:
        """Create a new Type.

        Args:
            valueType: The TealType (uint64 or bytes) that this ABI type will store in its internal
                ScratchVar.
        """
        super().__init__()
        self.stored_value = ScratchVar(valueType)

    @abstractmethod
    def has_same_type_as(self, other: "Type") -> bool:
        """Check if this type is considered equal to the other ABI type, irrespective of their
        values.

        Args:
            other: The ABI type to compare to.

        Returns:
            True if and only if self and other can store the same ABI value.
        """
        pass

    @abstractmethod
    def new_instance(self: T) -> T:
        """Create a new instance of this ABI type.

        The value of this type will not be applied to the new type.
        """
        pass

    @abstractmethod
    def is_dynamic(self) -> bool:
        """Check if this ABI type is dynamic.
        
        If a type is dynamic, the length of its encoding depends on its value. Otherwise, the type
        is considered static (not dynamic).
        """
        pass

    @abstractmethod
    def byte_length_static(self) -> int:
        """Get the byte length of this ABI type's encoding. Only valid for static types."""
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

    @abstractmethod
    def __str__(self) -> str:
        """Get the string representation of this ABI type, used for creating method signatures."""
        pass


Type.__module__ = "pyteal"


class ComputedType(ABC, Generic[T]):
    def __init__(self, producedType: T) -> None:
        super().__init__()
        self._producedType = producedType

    @abstractmethod
    def store_into(self, output: T) -> Expr:
        pass

    def use(self, action: Callable[[T], Expr]) -> Expr:
        newInstance = self._producedType.new_instance()
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
