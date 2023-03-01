from inspect import get_annotations
from typing import (
    List,
    Sequence,
    Dict,
    Generic,
    TypeVar,
    cast,
    overload,
    Any,
    TypeAlias,
    get_args,
    get_origin,
)
from collections import OrderedDict

from pyteal.types import TealType
from pyteal.errors import TealInputError, TealInternalError
from pyteal.ast.expr import Expr
from pyteal.ast.seq import Seq
from pyteal.ast.int import Int
from pyteal.ast.bytes import Bytes
from pyteal.ast.unaryexpr import Len
from pyteal.ast.binaryexpr import ExtractUint16
from pyteal.ast.naryexpr import Concat
from pyteal.ast.abstractvar import alloc_abstract_var

from pyteal.ast.abi.type import TypeSpec, BaseType, ComputedValue
from pyteal.ast.abi.bool import (
    Bool,
    BoolTypeSpec,
    _consecutive_bool_instance_num,
    _consecutive_bool_type_spec_num,
    _bool_sequence_length,
    _encode_bool_sequence,
    _bool_aware_static_byte_length,
)
from pyteal.ast.abi.uint import NUM_BITS_IN_BYTE, Uint16
from pyteal.ast.abi.util import substring_for_decoding, type_spec_from_annotation


def _encode_tuple(values: Sequence[BaseType]) -> Expr:
    heads: List[Expr] = []
    head_length_static: int = 0

    dynamicValueIndexToHeadIndex: Dict[int, int] = dict()
    ignoreNext = 0
    for i, elem in enumerate(values):
        if ignoreNext > 0:
            ignoreNext -= 1
            continue

        elemType = elem.type_spec()

        if elemType == BoolTypeSpec():
            numBools = _consecutive_bool_instance_num(values, i)
            ignoreNext = numBools - 1
            head_length_static += _bool_sequence_length(numBools)
            heads.append(
                _encode_bool_sequence(cast(Sequence[Bool], values[i : i + numBools]))
            )
            continue

        if elemType.is_dynamic():
            head_length_static += 2
            dynamicValueIndexToHeadIndex[i] = len(heads)
            heads.append(Seq())  # a placeholder
            continue

        head_length_static += elemType.byte_length_static()
        heads.append(elem.encode())

    tail_offset = Uint16()
    tail_offset_accumulator = Uint16()
    tail_holder = alloc_abstract_var(TealType.bytes)
    encoded_tail = alloc_abstract_var(TealType.bytes)

    firstDynamicTail = True
    for i, elem in enumerate(values):
        if elem.type_spec().is_dynamic():
            if firstDynamicTail:
                firstDynamicTail = False
                updateVars = Seq(
                    tail_holder.store(encoded_tail.load()),
                    tail_offset.set(head_length_static),
                )
            else:
                updateVars = Seq(
                    tail_holder.store(Concat(tail_holder.load(), encoded_tail.load())),
                    tail_offset.set(tail_offset_accumulator),
                )

            notLastDynamicValue = any(
                [nextValue.type_spec().is_dynamic() for nextValue in values[i + 1 :]]
            )
            if notLastDynamicValue:
                updateAccumulator = tail_offset_accumulator.set(
                    tail_offset.get() + Len(encoded_tail.load())
                )
            else:
                updateAccumulator = Seq()

            heads[dynamicValueIndexToHeadIndex[i]] = Seq(
                encoded_tail.store(elem.encode()),
                updateVars,
                updateAccumulator,
                tail_offset.encode(),
            )

    toConcat = heads
    if not firstDynamicTail:
        toConcat.append(tail_holder.load())

    if len(toConcat) == 0:
        return Bytes("")

    return Concat(*toConcat)


def _index_tuple(
    value_types: Sequence[TypeSpec], encoded: Expr, index: int, output: BaseType
) -> Expr:
    if not (0 <= index < len(value_types)):
        raise ValueError("Index outside of range")

    offset = 0
    ignoreNext = 0
    lastBoolStart = 0
    lastBoolLength = 0
    for i, typeBefore in enumerate(value_types[:index]):
        if ignoreNext > 0:
            ignoreNext -= 1
            continue

        if typeBefore == BoolTypeSpec():
            lastBoolStart = offset
            lastBoolLength = _consecutive_bool_type_spec_num(value_types, i)
            offset += _bool_sequence_length(lastBoolLength)
            ignoreNext = lastBoolLength - 1
            continue

        if typeBefore.is_dynamic():
            offset += 2
            continue

        offset += typeBefore.byte_length_static()

    valueType = value_types[index]
    if output.type_spec() != valueType:
        raise TypeError("Output type does not match value type")

    if type(output) is Bool:
        if ignoreNext > 0:
            # value is in the middle of a bool sequence
            bitOffsetInBoolSeq = lastBoolLength - ignoreNext
            bitOffsetInEncoded = lastBoolStart * NUM_BITS_IN_BYTE + bitOffsetInBoolSeq
        else:
            # value is the beginning of a bool sequence (or a single bool)
            bitOffsetInEncoded = offset * NUM_BITS_IN_BYTE
        return output.decode_bit(encoded, Int(bitOffsetInEncoded))

    if valueType.is_dynamic():
        hasNextDynamicValue = False
        nextDynamicValueOffset = offset + 2
        ignoreNext = 0
        for i, typeAfter in enumerate(value_types[index + 1 :], start=index + 1):
            if ignoreNext > 0:
                ignoreNext -= 1
                continue

            if type(typeAfter) is BoolTypeSpec:
                boolLength = _consecutive_bool_type_spec_num(value_types, i)
                nextDynamicValueOffset += _bool_sequence_length(boolLength)
                ignoreNext = boolLength - 1
                continue

            if typeAfter.is_dynamic():
                hasNextDynamicValue = True
                break

            nextDynamicValueOffset += typeAfter.byte_length_static()

        start_index = ExtractUint16(encoded, Int(offset))
        if not hasNextDynamicValue:
            # This is the final dynamic value, so decode the substring from start_index to the end of
            # encoded
            return output.decode(encoded, start_index=start_index)

        # There is a dynamic value after this one, and end_index is where its tail starts, so decode
        # the substring from start_index to end_index
        end_index = ExtractUint16(encoded, Int(nextDynamicValueOffset))
        return output.decode(encoded, start_index=start_index, end_index=end_index)

    start_index = Int(offset)
    length = Int(valueType.byte_length_static())

    if index + 1 == len(value_types):
        if offset == 0:
            # This is the first and only value in the tuple, so decode all of encoded
            return output.decode(encoded)
        if all(not x.is_dynamic() for x in value_types):
            # This is the last element in tuple with all elements being static typed
            return output.decode(encoded, start_index=start_index)

    if offset == 0:
        # This is the first value in the tuple, so decode the substring from 0 with length length
        return output.decode(encoded, length=length)

    # This is not the first or last value, so decode the substring from start_index with length length
    return output.decode(encoded, start_index=start_index, length=length)


class TupleTypeSpec(TypeSpec):
    def __init__(self, *value_type_specs: TypeSpec) -> None:
        super().__init__()
        self.value_specs = list(value_type_specs)

    def value_type_specs(self) -> List[TypeSpec]:
        """Get the TypeSpecs for the values of this tuple."""
        return self.value_specs

    def length_static(self) -> int:
        """Get the number of values this tuple holds."""
        return len(self.value_specs)

    def new_instance(self) -> "Tuple":
        match self.length_static():
            case 0:
                return Tuple0()
            case 1:
                return Tuple1(self)
            case 2:
                return Tuple2(self)
            case 3:
                return Tuple3(self)
            case 4:
                return Tuple4(self)
            case 5:
                return Tuple5(self)
            case _:
                return Tuple(self)

    def annotation_type(self) -> "type[Tuple]":
        vtses = self.value_type_specs()

        def annotater():
            return [x.annotation_type() for x in vtses]

        match len(vtses):
            case 0:
                return Tuple0
            case 1:
                v0 = annotater()[0]
                return Tuple1[v0]  # type: ignore[valid-type]
            case 2:
                v0, v1 = annotater()
                return Tuple2[v0, v1]  # type: ignore[valid-type]
            case 3:
                v0, v1, v2 = annotater()
                return Tuple3[v0, v1, v2]  # type: ignore[valid-type]
            case 4:
                v0, v1, v2, v3 = annotater()
                return Tuple4[v0, v1, v2, v3]  # type: ignore[valid-type]
            case 5:
                v0, v1, v2, v3, v4 = annotater()
                return Tuple5[v0, v1, v2, v3, v4]  # type: ignore[valid-type]

        raise TypeError(f"Cannot annotate tuple of length {len(vtses)}")

    def is_dynamic(self) -> bool:
        return any(type_spec.is_dynamic() for type_spec in self.value_type_specs())

    def byte_length_static(self) -> int:
        if self.is_dynamic():
            raise ValueError("Type is dynamic")
        return _bool_aware_static_byte_length(self.value_type_specs())

    def storage_type(self) -> TealType:
        return TealType.bytes

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TupleTypeSpec)
            and self.value_type_specs() == other.value_type_specs()
        )

    def __str__(self) -> str:
        return "({})".format(",".join(map(str, self.value_type_specs())))


TupleTypeSpec.__module__ = "pyteal.abi"


class Tuple(BaseType):
    def __init__(self, tuple_type_spec: TupleTypeSpec) -> None:
        super().__init__(tuple_type_spec)

    def type_spec(self) -> TupleTypeSpec:
        return cast(TupleTypeSpec, super().type_spec())

    def decode(
        self,
        encoded: Expr,
        *,
        start_index: Expr | None = None,
        end_index: Expr | None = None,
        length: Expr | None = None,
    ) -> Expr:
        extracted = substring_for_decoding(
            encoded, start_index=start_index, end_index=end_index, length=length
        )
        return self._stored_value.store(extracted)

    @overload
    def set(self, *values: BaseType) -> Expr:
        pass

    @overload
    def set(self, values: ComputedValue["Tuple"]) -> Expr:
        # TODO: should support values as a Tuple as well
        pass

    def set(self, *values):
        """
        set(*values: BaseType) -> pyteal.Expr
        set(values: ComputedValue[Tuple]) -> pyteal.Expr

        Set the elements of this Tuple to the input values.

        The behavior of this method depends on the input argument type:

            * Variable number of :code:`BaseType` arguments: set the elements of this Tuple to the arguments to this method. A compiler error will occur if any argument does not match this Tuple's element type at the same index, or if the total argument count does not equal this Tuple's length.
            * :code:`ComputedValue[Tuple]`: copy the elements from a Tuple produced by a ComputedValue. The element types and length produced by the ComputedValue must exactly match this Tuple's element types and length, otherwise an error will occur.

        Args:
            values: The new elements this Tuple should have. This must follow the above constraints.

        Returns:
            An expression which stores the given value into this Tuple.
        """
        if len(values) == 1 and isinstance(values[0], ComputedValue):
            return self._set_with_computed_type(values[0])

        myTypes = self.type_spec().value_type_specs()
        if len(myTypes) != len(values):
            raise TealInputError(
                f"Incorrect length for values. Expected {len(myTypes)}, got {len(values)}"
            )
        for index, (value, myType) in enumerate(zip(values, myTypes)):
            if not isinstance(value, BaseType):
                raise TealInputError(f"Expected BaseType, got {value}")
            if myType != value.type_spec():
                raise TealInputError(
                    f"Input values do not match type at {index=}: {value.type_spec()} != {myType}"
                )
        return self._stored_value.store(_encode_tuple(values))

    def encode(self) -> Expr:
        return self._stored_value.load()

    def length(self) -> Expr:
        """Get the number of values this tuple holds as an Expr."""
        return Int(self.type_spec().length_static())

    def __getitem__(self, index: int) -> "TupleElement[Any]":
        """Retrieve an element by its index in this Tuple.

        Indexes start at 0.

        Args:
            index: a Python integer containing the index to access. This function will raise an error
                if its value is negative or if the index is equal to or greater than the length of
                this Tuple.

        Returns:
            A TupleElement that corresponds to the element at the given index. This type is a
            ComputedValue. Due to Python type limitations, the parameterized type of the
            TupleElement is Any.
        """
        if not (0 <= index < self.type_spec().length_static()):
            raise TealInputError(f"Index out of bounds: {index}")
        return TupleElement(self, index)


Tuple.__module__ = "pyteal.abi"

T = TypeVar("T", bound=BaseType)


class TupleElement(ComputedValue[T]):
    """Represents the extraction of a specific element from a Tuple."""

    def __init__(self, tuple: Tuple, index: int) -> None:
        super().__init__()
        self.tuple = tuple
        self.index = index

    def produced_type_spec(self) -> TypeSpec:
        return self.tuple.type_spec().value_type_specs()[self.index]

    def store_into(self, output: T) -> Expr:
        return _index_tuple(
            self.tuple.type_spec().value_type_specs(),
            self.tuple.encode(),
            self.index,
            output,
        )


TupleElement.__module__ = "pyteal.abi"

# Until Python 3.11 is released with support for PEP 646 -- Variadic Generics, it's not possible for
# the Tuple class to take an arbitrary number of template parameters. As a workaround, we define the
# following classes for specifically sized Tuples. If needed, more classes can be added for larger
# sizes.


def _tuple_raise_arg_mismatch(expected: int, typespec: TupleTypeSpec):
    if len(typespec.value_specs) != expected:
        raise TealInputError(
            f"Expected TupleTypeSpec with {expected} elements, Got {len(typespec.value_specs)}"
        )


class Tuple0(Tuple):
    """A Tuple with 0 values."""

    def __init__(self) -> None:
        super().__init__(TupleTypeSpec())


Tuple0.__module__ = "pyteal.abi"

T1 = TypeVar("T1", bound=BaseType)


class Tuple1(Tuple, Generic[T1]):
    """A Tuple with 1 value."""

    def __init__(self, value_type_spec: TupleTypeSpec) -> None:
        _tuple_raise_arg_mismatch(1, value_type_spec)
        super().__init__(value_type_spec)


Tuple1.__module__ = "pyteal.abi"

T2 = TypeVar("T2", bound=BaseType)


class Tuple2(Tuple, Generic[T1, T2]):
    """A Tuple with 2 values."""

    def __init__(self, value_type_spec: TupleTypeSpec) -> None:
        _tuple_raise_arg_mismatch(2, value_type_spec)
        super().__init__(value_type_spec)


Tuple2.__module__ = "pyteal.abi"

T3 = TypeVar("T3", bound=BaseType)


class Tuple3(Tuple, Generic[T1, T2, T3]):
    """A Tuple with 3 values."""

    def __init__(
        self,
        value_type_spec: TupleTypeSpec,
    ) -> None:
        _tuple_raise_arg_mismatch(3, value_type_spec)
        super().__init__(value_type_spec)


Tuple3.__module__ = "pyteal.abi"

T4 = TypeVar("T4", bound=BaseType)


class Tuple4(Tuple, Generic[T1, T2, T3, T4]):
    """A Tuple with 4 values."""

    def __init__(
        self,
        value_type_spec: TupleTypeSpec,
    ) -> None:
        _tuple_raise_arg_mismatch(4, value_type_spec)
        super().__init__(value_type_spec)


Tuple4.__module__ = "pyteal.abi"

T5 = TypeVar("T5", bound=BaseType)


class Tuple5(Tuple, Generic[T1, T2, T3, T4, T5]):
    """A Tuple with 5 values."""

    def __init__(
        self,
        value_type_spec: TupleTypeSpec,
    ) -> None:
        _tuple_raise_arg_mismatch(5, value_type_spec)
        super().__init__(value_type_spec)


Tuple5.__module__ = "pyteal.abi"


Field: TypeAlias = TupleElement[T]


class NamedTupleTypeSpec(TupleTypeSpec):
    """A NamedTupleType inherits from TupleTypeSpec, allowing for more than 5 elements."""

    def __init__(
        self, instance_class: type["NamedTuple"], *value_type_specs: TypeSpec
    ) -> None:
        if instance_class == NamedTuple:
            raise TealInputError(
                "NamedTupleTypeSpec must be instanced with subclassed NamedTuple class."
            )

        self.instance_class: type["NamedTuple"] = instance_class
        super().__init__(*value_type_specs)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, NamedTupleTypeSpec)
            and self.instance_class == other.instance_class
            and self.value_type_specs() == other.value_type_specs()
        )

    def annotation_type(self) -> "type[NamedTuple]":
        return self.instance_class

    def new_instance(self) -> "NamedTuple":
        return self.instance_class()


NamedTupleTypeSpec.__module__ = "pyteal.abi"


class NamedTuple(Tuple):
    """A NamedTuple is a :any:`Tuple` that has named elements, inspired by Python's `typing.NamedTuple <https://docs.python.org/3/library/typing.html#typing.NamedTuple>`_.

    A new NamedTuple type can be created by subclassing this class and adding field annotations.
    Every field annotation must be an instantiable ABI type wrapped in the :code:`abi.Field` annotation.

    For example:

        .. code-block:: python

            from pyteal import *

            class User(abi.NamedTuple):
                address: abi.Field[abi.Address]
                balance: abi.Field[abi.Uint64]

            # User is equivalent to abi.Tuple2[abi.Address, abi.Uint64]

            my_user = User()

    .. automethod:: __init_subclass__
    .. automethod:: __getattr__
    """

    def __init_subclass__(cls) -> None:
        """This method ensures one only constructs directly from `NamedTuple`,
        rather than inheriting from `NamedTuple`'s inheritance.

        We want to prohibit the following examples:

            .. code-block:: python

                from pyteal import *

                class LegalInheritance(abi.NamedTuple):
                    a: abi.Field[abi.Uint64]

                # following are bad cases we guard against

                class IllegalInheritance0(LegalInheritance):
                    a: abi.Field[abi.Uint64]

                class IllegalInheritance1(LegalInheritance, abi.NamedTuple):
                    a: abi.Field[abi.Uint64]
        """
        is_named_tuple_in_bases = False

        for base_t in cls.__bases__:
            if base_t == NamedTuple:
                is_named_tuple_in_bases = True
            elif issubclass(base_t, NamedTuple):
                raise TealInternalError(
                    f"Cannot construct {cls} by inheriting {cls.__bases__}. "
                    f"Must be constructed by direct inheritance from NamedTuple"
                )

        if not is_named_tuple_in_bases:
            raise TealInternalError(
                "Unexpected: did not find NamedTuple in __bases__,"
                "did not find NamedTuple in __bases__ member's __bases__"
            )

        super().__init_subclass__()

    def __init__(self):
        if type(self) is NamedTuple:
            raise TealInputError("NamedTuple must be subclassed")

        anns = get_annotations(type(self))
        if not anns:
            raise TealInputError("Expected fields to be declared but found none")

        # NOTE: this `_ready` variable enables `__setattr__` during `__init__` execution,
        # while after `__init__`, we cannot use `__setattr__` to set fields in `NamedTuple`.
        # NOTE: If we declare variable `__ready`, then internally,
        # the variable name would be changed to `_NamedTuple__ready`, which is implicit.
        self.__ready = False
        self.__type_specs: OrderedDict[str, TypeSpec] = OrderedDict()
        self.__field_index: dict[str, int] = {}

        for index, (name, annotation) in enumerate(anns.items()):
            origin = get_origin(annotation)
            if origin is None:
                origin = annotation
            if origin is not get_origin(Field):
                raise TealInputError(
                    f'Type annotation for attribute "{name}" must be a Field. Got {origin}'
                )

            args = get_args(annotation)
            if len(args) != 1:
                raise TealInputError(
                    f'Type annotation for attribute "{name}" must have a single argument. Got {args}'
                )

            self.__type_specs[name] = type_spec_from_annotation(args[0])
            self.__field_index[name] = index

        super().__init__(
            NamedTupleTypeSpec(type(self), *list(self.__type_specs.values()))
        )

        self.__ready = True

    def __getattr__(self, field: str) -> TupleElement[Any]:
        """Retrieve an element by its field in this NamedTuple.

        For example:

        .. code-block:: python

            from pyteal import *

            class User(abi.NamedTuple):
                address: abi.Field[abi.Address]
                balance: abi.Field[abi.Uint64]

            @ABIReturnSubroutine
            def get_user_balance(user: User, *, output: abi.Uint64) -> Expr:
                return output.set(user.balance)

        Args:
            field: a Python string containing the field to access.
                This function will raise an KeyError if the field is not available in the defined NamedTuple.

        Returns:
            A TupleElement that corresponds to the element at the given field name, returning a ComputedType.
            Due to Python type limitations, the parameterized type of the TupleElement is Any.
        """
        return self.__getitem__(self.__field_index[field])

    def __setattr__(self, name: str, field: Any) -> None:
        # we allow `__setattr__` only when:
        # - we are in `__init__`: `not self.__ready`
        # - we are setting `_ready`: `name == "_NamedTuple__ready"`,
        #   it is internally changed from `__ready` to `_NamedTuple__ready`,
        #   see notes in `__init__`
        if name == "_NamedTuple__ready" or not self.__ready:
            super().__setattr__(name, field)
            return
        # NOTE this pass condition is for following scenario:
        # NamedTuple is an argument, and inside subroutine, subroutine set internal ABI value with FrameStorage
        # This used to violate `__setattr__` for not allowing any assignment to attributes
        # Now this case is lifted such that we can shift the storage scheme.
        if name == "_stored_value" and self.__ready:
            super().__setattr__(name, field)
            return
        raise TealInputError("cannot assign to NamedTuple attributes.")


NamedTuple.__module__ = "pyteal.abi"
