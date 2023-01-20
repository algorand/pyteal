from typing import TypeVar, Generic, Callable, Final, cast
from abc import ABC, abstractmethod

from pyteal.ast.expr import Expr
from pyteal.ast.abstractvar import AbstractVar, alloc_abstract_var
from pyteal.ast.seq import Seq
from pyteal.errors import TealInputError, TealTypeError
from pyteal.types import TealType


class TypeSpec(ABC):
    """TypeSpec represents a specification for an ABI type.

    Essentially this is a factory that can produce specific instances of ABI types.
    """

    @abstractmethod
    def new_instance(self) -> "BaseType":
        """Create a new instance of the specified type."""
        pass

    @abstractmethod
    def annotation_type(self) -> "type[BaseType]":
        """Get the annotation type associated with this spec"""
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
    def storage_type(self) -> TealType:
        """Get the TealType that the underlying ScratchVar should hold for this type."""
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """Check if this type is considered equal to another ABI type.

        Args:
            other: The object to compare to. If this is not a TypeSpec, this method will never
                return true.

        Returns:
            True if and only if self and other represent the same ABI type.
        """
        pass

    @abstractmethod
    def __str__(self) -> str:
        """Get the string representation of this ABI type, used for creating method signatures."""
        pass


TypeSpec.__module__ = "pyteal.abi"


class BaseType(ABC):
    """The abstract base class for all ABI type instances.

    The value of the type is contained in a unique ScratchVar that only this instance has access to.
    As a result, the value of an ABI type is mutable and can be efficiently referenced multiple
    times without needing to recompute it.
    """

    def __init__(self, spec: TypeSpec) -> None:
        """Create a new BaseType."""
        super().__init__()
        self._type_spec: Final[TypeSpec] = spec
        self._stored_value: AbstractVar = alloc_abstract_var(spec.storage_type())

    def type_spec(self) -> TypeSpec:
        """Get the TypeSpec for this ABI type instance."""
        return self._type_spec

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
        start_index: Expr | None = None,
        end_index: Expr | None = None,
        length: Expr | None = None,
    ) -> Expr:
        """Decode a substring of the passed in encoded string and set it as this type's value.

        The arguments to this function are means to be as flexible as possible for the caller.
        Multiple types of substrings can be specified based on the arguments, as listed below:

        * Entire string: if start_index, end_index, and length are all None, the entire encoded string
          is decoded.
        * Prefix: if start_index is None and one of end_index or length is provided, a prefix of the
          encoded string is decoded. The range is 0 through end_index or length (they are equivalent).
        * Suffix: if start_index is provided and end_index and length are None, a suffix of the encoded
          string is decoded. The range is start_index through the end of the string.
        * Substring specified with end_index: if start_index and end_index are provided and length is
          None, a substring of the encoded string is decoded. The range is start_index through
          end_index.
        * Substring specified with length: if start_index and length are provided and end_index is
          None, a substring of the encoded string is decoded. The range is start_index through
          start_index+length.

        Args:
            encoded: An expression containing the bytes to decode. Must evaluate to TealType.bytes.
            start_index (optional): An expression containing the index to start decoding. Must
                evaluate to TealType.uint64. Defaults to None.
            end_index (optional): An expression containing the index to stop decoding. Must evaluate
                to TealType.uint64. Defaults to None.
            length (optional): An expression containing the length of the substring to decode. Must
                evaluate to TealType.uint64. Defaults to None.

        Returns:
            An expression that performs the necessary steps in order to decode the given string into
            a value.
        """
        pass

    def _set_with_computed_type(self, value: "ComputedValue[BaseType]") -> Expr:
        target_type_spec = value.produced_type_spec()
        if self.type_spec() != target_type_spec:
            raise TealInputError(
                f"Cannot set {self.type_spec()} with ComputedType of {target_type_spec}"
            )
        return value.store_into(self)

    def __str__(self) -> str:
        return str(self.type_spec())


BaseType.__module__ = "pyteal.abi"

T_co = TypeVar("T_co", bound=BaseType, covariant=True)


class ComputedValue(ABC, Generic[T_co]):
    """Represents an ABI Type whose value must be computed by an expression."""

    @abstractmethod
    def produced_type_spec(self) -> TypeSpec:
        """Get the ABI TypeSpec that this object produces."""
        pass

    @abstractmethod
    def store_into(self, output: T_co) -> Expr:  # type: ignore[misc]
        """Compute the value and store it into an existing ABI type instance.

        NOTE: If you call this method multiple times, the computation to determine the value will be
        repeated each time. For this reason, it is recommended to only issue a single call to either
        :code:`store_into` or :code:`use`.

        Args:
            output: The object where the computed value will be stored. This object must have the
                same type as this class's produced type.

        Returns:
            An expression which stores the computed value represented by this class into the output
            object.
        """
        pass

    def use(self, action: Callable[[T_co], Expr]) -> Expr:
        """Compute the value and pass it to a callable expression.

        NOTE: If you call this method multiple times, the computation to determine the value will be
        repeated each time. For this reason, it is recommended to only issue a single call to either
        :code:`store_into` or :code:`use`.

        Args:
            action: A callable object that will receive an instance of this class's produced type
                with the computed value. The callable object may use that value as it sees fit, but
                it must return an Expr to be included in the program's AST.

        Returns:
            An expression which contains the returned expression from invoking `action` with the
            computed value.
        """
        newInstance = cast(T_co, self.produced_type_spec().new_instance())
        return Seq(self.store_into(newInstance), action(newInstance))


ComputedValue.__module__ = "pyteal.abi"


class ReturnedValue(ComputedValue):
    def __init__(self, type_spec: TypeSpec, computation_expr: Expr):
        from pyteal.ast.subroutine import SubroutineCall

        self.type_spec = type_spec
        if not isinstance(computation_expr, SubroutineCall):
            raise TealInputError(
                f"Expecting computation_expr to be SubroutineCall but get {type(computation_expr)}"
            )
        self.computation = computation_expr

    def produced_type_spec(self) -> TypeSpec:
        return self.type_spec

    def store_into(self, output: BaseType) -> Expr:
        from pyteal.ast.subroutine import SubroutineDeclaration

        if output.type_spec() != self.produced_type_spec():
            raise TealInputError(
                f"expected type_spec {self.produced_type_spec()} but get {output.type_spec()}"
            )

        # HANG NOTE! This get_declaration check applies only for pre frame pointer case
        # the post frame pointer case should not apply
        # need to somehow expose the context of evaluation

        declaration: SubroutineDeclaration | None = None
        try:
            declaration = self.computation.subroutine.get_declaration_by_option(False)
        except Exception:
            pass

        if declaration is not None:
            if declaration.deferred_expr is None:
                raise TealInputError(
                    "ABI return subroutine must have deferred_expr to be not-None."
                )
            if declaration.deferred_expr.type_of() != output.type_spec().storage_type():
                raise TealTypeError(
                    declaration.deferred_expr.type_of(),
                    output.type_spec().storage_type(),
                )

        return output._stored_value.store(self.computation)


ReturnedValue.__module__ = "pyteal.abi"
