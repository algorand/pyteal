from typing import Sequence, TypeVar, Any, Literal, get_origin, get_args, cast

import algosdk.abi

from pyteal.errors import TealInputError
from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from pyteal.ast.substring import Extract, Substring, Suffix
from pyteal.ast.abi.type import TypeSpec, BaseType


def substringForDecoding(
    encoded: Expr,
    *,
    startIndex: Expr = None,
    endIndex: Expr = None,
    length: Expr = None,
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
    from pyteal.ast.abi.bool import BoolTypeSpec, Bool
    from pyteal.ast.abi.uint import (
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
    from pyteal.ast.abi.array_dynamic import DynamicArrayTypeSpec, DynamicArray
    from pyteal.ast.abi.array_static import StaticArrayTypeSpec, StaticArray
    from pyteal.ast.abi.tuple import (
        TupleTypeSpec,
        Tuple,
        Tuple0,
        Tuple1,
        Tuple2,
        Tuple3,
        Tuple4,
        Tuple5,
    )
    from pyteal.ast.abi.string import StringTypeSpec, String
    from pyteal.ast.abi.address import AddressTypeSpec, Address
    from pyteal.ast.abi.transaction import (
        Transaction,
        TransactionTypeSpec,
        PaymentTransaction,
        PaymentTransactionTypeSpec,
        KeyRegisterTransaction,
        KeyRegisterTransactionTypeSpec,
        AssetConfigTransaction,
        AssetConfigTransactionTypeSpec,
        AssetFreezeTransaction,
        AssetFreezeTransactionTypeSpec,
        AssetTransferTransaction,
        AssetTransferTransactionTypeSpec,
        ApplicationCallTransaction,
        ApplicationCallTransactionTypeSpec,
    )
    from pyteal.ast.abi.reference_type import (
        AccountTypeSpec,
        Account,
        AssetTypeSpec,
        Asset,
        ApplicationTypeSpec,
        Application,
    )

    origin = get_origin(annotation)
    if origin is None:
        origin = annotation

    args = get_args(annotation)

    if origin is Account:
        if len(args) != 0:
            raise TypeError("Account expects 0 arguments. Got: {}".format(args))
        return AccountTypeSpec()

    if origin is Asset:
        if len(args) != 0:
            raise TypeError("Asset expects 0 argsuments. Got: {}".format(args))
        return AssetTypeSpec()

    if origin is Application:
        if len(args) != 0:
            raise TypeError("Application expects 0 argsuments. Got: {}".format(args))
        return ApplicationTypeSpec()

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

    if origin is String:
        if len(args) != 0:
            raise TypeError("String expects 0 arguments. Got: {}".format(args))
        return StringTypeSpec()

    if origin is Address:
        if len(args) != 0:
            raise TypeError("Address expects 0 arguments. Got: {}".format(args))
        return AddressTypeSpec()

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

    if origin is Transaction:
        if len(args) != 0:
            raise TypeError(
                "Transaction expects 0 type arguements. Got {}".format(args)
            )
        return TransactionTypeSpec()

    if origin is PaymentTransaction:
        if len(args) != 0:
            raise TypeError(
                "PaymentTransaction expects 0 type arguements. Got {}".format(args)
            )
        return PaymentTransactionTypeSpec()

    if origin is KeyRegisterTransaction:
        if len(args) != 0:
            raise TypeError(
                "KeyRegisterTransaction expects 0 type arguements. Got {}".format(args)
            )
        return KeyRegisterTransactionTypeSpec()

    if origin is AssetConfigTransaction:
        if len(args) != 0:
            raise TypeError(
                "AssetConfigTransaction expects 0 type arguements. Got {}".format(args)
            )
        return AssetConfigTransactionTypeSpec()

    if origin is AssetFreezeTransaction:
        if len(args) != 0:
            raise TypeError(
                "AssetFreezeTransaction expects 0 type arguements. Got {}".format(args)
            )
        return AssetFreezeTransactionTypeSpec()

    if origin is AssetTransferTransaction:
        if len(args) != 0:
            raise TypeError(
                "AssetTransferTransaction expects 0 type arguements. Got {}".format(
                    args
                )
            )
        return AssetTransferTransactionTypeSpec()

    if origin is ApplicationCallTransaction:
        if len(args) != 0:
            raise TypeError(
                "ApplicationCallTransaction expects 0 type arguements. Got {}".format(
                    args
                )
            )
        return ApplicationCallTransactionTypeSpec()

    raise TypeError("Unknown annotation origin: {}".format(origin))


T = TypeVar("T", bound=BaseType)


def contains_type_spec(ts: TypeSpec, targets: Sequence[TypeSpec]) -> bool:
    from pyteal.ast.abi.array_dynamic import DynamicArrayTypeSpec
    from pyteal.ast.abi.array_static import StaticArrayTypeSpec
    from pyteal.ast.abi.tuple import TupleTypeSpec

    stack: list[TypeSpec] = [ts]

    while stack:
        current = stack.pop()
        if current in targets:
            return True

        match current:
            case TupleTypeSpec():
                stack.extend(current.value_type_specs())
            case DynamicArrayTypeSpec():
                stack.append(current.value_type_spec())
            case StaticArrayTypeSpec():
                stack.append(current.value_type_spec())

    return False


def size_of(t: type[T]) -> int:
    """Get the size in bytes of an ABI type. Must be a static type"""

    ts = type_spec_from_annotation(t)
    if ts.is_dynamic():
        raise TealInputError("Cannot get size of dynamic type")

    return ts.byte_length_static()


def make(t: type[T]) -> T:
    """Create a new instance of an ABI type. The type to create is determined by the input argument,
    which must be a fully-specified type's class. Fully-specified means that every generic argument
    is given a value.

    For example:
        .. code-block:: python

                # both of these are equivalent
                a = abi.make(abi.Tuple2[abi.Uint64, abi.StaticArray[abi.Bool, Literal[8]]])
                b = abi.TupleTypeSpec(abi.Uint64TypeSpec(), abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 8))

    This is purely a convenience method over instantiating the type directly, which can be cumbersome
    due to the lengthy TypeSpec class names.

    Args:
        t: A fully-specified subclass of abi.BaseType.

    Returns:
        A new instance of the given type class.
    """
    return cast(T, type_spec_from_annotation(t).new_instance())


def algosdk_from_type_spec(t: TypeSpec) -> algosdk.abi.ABIType:
    from pyteal.ast.abi import ReferenceTypeSpecs, TransactionTypeSpecs

    if t in TransactionTypeSpecs:
        raise TealInputError(
            f"cannot map ABI transaction type spec {t!r} to an appropriate algosdk ABI type"
        )

    if t in ReferenceTypeSpecs:
        raise TealInputError(
            f"cannot map ABI reference type spec {t!r} to an appropriate algosdk ABI type"
        )

    return algosdk.abi.ABIType.from_string(str(t))


def algosdk_from_annotation(t: type[T]) -> algosdk.abi.ABIType:
    return algosdk_from_type_spec(type_spec_from_annotation(t))
