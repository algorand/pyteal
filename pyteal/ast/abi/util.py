from typing import Any, Literal, get_origin, get_args

from ...errors import TealInputError
from ..expr import Expr
from ..int import Int
from ..substring import Extract, Substring, Suffix
from .type import TypeSpec


def substringForDecoding(
    encoded: Expr,
    *,
    startIndex: Expr = None,
    endIndex: Expr = None,
    length: Expr = None
) -> Expr:
    """A helper function for getting the substring to decode according to the rules of BaseType.decode."""
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


def int_literal_from_annotation(annotation: Any) -> int:
    """Extract an integer from a Literal type annotation.

    Args:
        annotation: A Literal type annotation. E.g., `Literal[4]`. This must contain only a single
            integer value.

    Returns:
        The integer that the Literal represents.
    """
    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is not Literal:
        raise TypeError("Expected literal for argument. Got: {}".format(origin))

    if len(args) != 1 or type(args[0]) is not int:
        raise TypeError(
            "Expected single integer argument for Literal. Got: {}".format(args)
        )

    return args[0]


def type_spec_from_annotation(annotation: Any) -> TypeSpec:
    """Convert an ABI type annotation into the corresponding TypeSpec.

    For example, calling this function with the input `abi.StaticArray[abi.Bool, Literal[5]]` would
    return `abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 5)`.

    Args:
        annotation. An annotation representing an ABI type instance.

    Raises:
        TypeError: if the input annotation does not represent a valid ABI type instance or its
            arguments are invalid.

    Returns:
        The TypeSpec that corresponds to the input annotation.
    """
    from .bool import BoolTypeSpec, Bool
    from .uint import (
        ByteTypeSpec,
        Byte,
        Uint8TypeSpec,
        Uint8,
        Uint16TypeSpec,
        Uint16,
        Uint32TypeSpec,
        Uint32,
        Uint64TypeSpec,
        Uint64,
    )
    from .array_dynamic import DynamicArrayTypeSpec, DynamicArray
    from .array_static import StaticArrayTypeSpec, StaticArray
    from .tuple import (
        TupleTypeSpec,
        Tuple,
        Tuple0,
        Tuple1,
        Tuple2,
        Tuple3,
        Tuple4,
        Tuple5,
    )

    origin = get_origin(annotation)
    if origin is None:
        origin = annotation

    args = get_args(annotation)

    if origin is Bool:
        if len(args) != 0:
            raise TypeError("Bool expects 0 type arguments. Got: {}".format(args))
        return BoolTypeSpec()

    if origin is Byte:
        if len(args) != 0:
            raise TypeError("Byte expects 0 type arguments. Got: {}".format(args))
        return ByteTypeSpec()

    if origin is Uint8:
        if len(args) != 0:
            raise TypeError("Uint8 expects 0 type arguments. Got: {}".format(args))
        return Uint8TypeSpec()

    if origin is Uint16:
        if len(args) != 0:
            raise TypeError("Uint16 expects 0 type arguments. Got: {}".format(args))
        return Uint16TypeSpec()

    if origin is Uint32:
        if len(args) != 0:
            raise TypeError("Uint32 expects 0 type arguments. Got: {}".format(args))
        return Uint32TypeSpec()

    if origin is Uint64:
        if len(args) != 0:
            raise TypeError("Uint64 expects 0 type arguments. Got: {}".format(args))
        return Uint64TypeSpec()

    if origin is DynamicArray:
        if len(args) != 1:
            raise TypeError(
                "DynamicArray expects 1 type argument. Got: {}".format(args)
            )
        value_type_spec = type_spec_from_annotation(args[0])
        return DynamicArrayTypeSpec(value_type_spec)

    if origin is StaticArray:
        if len(args) != 2:
            raise TypeError("StaticArray expects 1 type argument. Got: {}".format(args))
        value_type_spec = type_spec_from_annotation(args[0])
        array_length = int_literal_from_annotation(args[1])
        return StaticArrayTypeSpec(value_type_spec, array_length)

    if origin is Tuple:
        return TupleTypeSpec(*(type_spec_from_annotation(arg) for arg in args))

    if origin is Tuple0:
        if len(args) != 0:
            raise TypeError("Tuple0 expects 0 type arguments. Got: {}".format(args))
        return TupleTypeSpec()

    if origin is Tuple1:
        if len(args) != 1:
            raise TypeError("Tuple1 expects 1 type argument. Got: {}".format(args))
        return TupleTypeSpec(*(type_spec_from_annotation(arg) for arg in args))

    if origin is Tuple2:
        if len(args) != 2:
            raise TypeError("Tuple2 expects 2 type arguments. Got: {}".format(args))
        return TupleTypeSpec(*(type_spec_from_annotation(arg) for arg in args))

    if origin is Tuple3:
        if len(args) != 3:
            raise TypeError("Tuple3 expects 3 type arguments. Got: {}".format(args))
        return TupleTypeSpec(*(type_spec_from_annotation(arg) for arg in args))

    if origin is Tuple4:
        if len(args) != 4:
            raise TypeError("Tuple4 expects 4 type arguments. Got: {}".format(args))
        return TupleTypeSpec(*(type_spec_from_annotation(arg) for arg in args))

    if origin is Tuple5:
        if len(args) != 5:
            raise TypeError("Tuple5 expects 5 type arguments. Got: {}".format(args))
        return TupleTypeSpec(*(type_spec_from_annotation(arg) for arg in args))

    raise TypeError("Unknown annotation origin: {}".format(origin))
