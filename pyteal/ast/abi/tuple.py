from typing import (
    List,
    Sequence,
    Dict,
    Generic,
    TypeVar,
    cast,
    overload,
)

from pyteal.types import TealType
from pyteal.errors import TealInputError
from pyteal.ast.expr import Expr
from pyteal.ast.seq import Seq
from pyteal.ast.int import Int
from pyteal.ast.bytes import Bytes
from pyteal.ast.unaryexpr import Len
from pyteal.ast.binaryexpr import ExtractUint16
from pyteal.ast.naryexpr import Concat
from pyteal.ast.scratchvar import ScratchVar

from pyteal.ast.abi.type import TypeSpec, BaseType, ComputedValue
from pyteal.ast.abi.bool import (
    Bool,
    BoolTypeSpec,
    consecutiveBoolInstanceNum,
    consecutiveBoolTypeSpecNum,
    boolSequenceLength,
    encodeBoolSequence,
    boolAwareStaticByteLength,
)
from pyteal.ast.abi.uint import NUM_BITS_IN_BYTE, Uint16
from pyteal.ast.abi.util import substringForDecoding


def encodeTuple(values: Sequence[BaseType]) -> Expr:
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
            numBools = consecutiveBoolInstanceNum(values, i)
            ignoreNext = numBools - 1
            head_length_static += boolSequenceLength(numBools)
            heads.append(
                encodeBoolSequence(cast(Sequence[Bool], values[i : i + numBools]))
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
    tail_holder = ScratchVar(TealType.bytes)
    encoded_tail = ScratchVar(TealType.bytes)

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


def indexTuple(
    valueTypes: Sequence[TypeSpec], encoded: Expr, index: int, output: BaseType
) -> Expr:
    if not (0 <= index < len(valueTypes)):
        raise ValueError("Index outside of range")

    offset = 0
    ignoreNext = 0
    lastBoolStart = 0
    lastBoolLength = 0
    for i, typeBefore in enumerate(valueTypes[:index]):
        if ignoreNext > 0:
            ignoreNext -= 1
            continue

        if typeBefore == BoolTypeSpec():
            lastBoolStart = offset
            lastBoolLength = consecutiveBoolTypeSpecNum(valueTypes, i)
            offset += boolSequenceLength(lastBoolLength)
            ignoreNext = lastBoolLength - 1
            continue

        if typeBefore.is_dynamic():
            offset += 2
            continue

        offset += typeBefore.byte_length_static()

    valueType = valueTypes[index]
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
        return output.decodeBit(encoded, Int(bitOffsetInEncoded))

    if valueType.is_dynamic():
        hasNextDynamicValue = False
        nextDynamicValueOffset = offset + 2
        ignoreNext = 0
        for i, typeAfter in enumerate(valueTypes[index + 1 :], start=index + 1):
            if ignoreNext > 0:
                ignoreNext -= 1
                continue

            if type(typeAfter) is BoolTypeSpec:
                boolLength = consecutiveBoolTypeSpecNum(valueTypes, i)
                nextDynamicValueOffset += boolSequenceLength(boolLength)
                ignoreNext = boolLength - 1
                continue

            if typeAfter.is_dynamic():
                hasNextDynamicValue = True
                break

            nextDynamicValueOffset += typeAfter.byte_length_static()

        startIndex = ExtractUint16(encoded, Int(offset))
        if not hasNextDynamicValue:
            # This is the final dynamic value, so decode the substring from startIndex to the end of
            # encoded
            return output.decode(encoded, start_index=startIndex)

        # There is a dynamic value after this one, and endIndex is where its tail starts, so decode
        # the substring from startIndex to endIndex
        endIndex = ExtractUint16(encoded, Int(nextDynamicValueOffset))
        return output.decode(encoded, start_index=startIndex, end_index=endIndex)

    startIndex = Int(offset)
    length = Int(valueType.byte_length_static())

    if index + 1 == len(valueTypes):
        if offset == 0:
            # This is the first and only value in the tuple, so decode all of encoded
            return output.decode(encoded)
        # This is the last value in the tuple, so decode the substring from startIndex to the end of
        # encoded
        return output.decode(encoded, start_index=startIndex)

    if offset == 0:
        # This is the first value in the tuple, so decode the substring from 0 with length length
        return output.decode(encoded, length=length)

    # This is not the first or last value, so decode the substring from startIndex with length length
    return output.decode(encoded, start_index=startIndex, length=length)


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
        return boolAwareStaticByteLength(self.value_type_specs())

    def storage_type(self) -> TealType:
        return TealType.bytes

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, TupleTypeSpec)
            and self.value_type_specs() == other.value_type_specs()
        )

    def __str__(self) -> str:
        return "({})".format(",".join(map(str, self.value_type_specs())))


TupleTypeSpec.__module__ = "pyteal"

T_tuple = TypeVar("T_tuple", bound="Tuple")


class Tuple(BaseType):
    def __init__(self, tuple_type_spec: TupleTypeSpec) -> None:
        super().__init__(tuple_type_spec)

    def type_spec(self) -> TupleTypeSpec:
        return cast(TupleTypeSpec, super().type_spec())

    def decode(
        self,
        encoded: Expr,
        *,
        start_index: Expr = None,
        end_index: Expr = None,
        length: Expr = None,
    ) -> Expr:
        extracted = substringForDecoding(
            encoded, startIndex=start_index, endIndex=end_index, length=length
        )
        return self.stored_value.store(extracted)

    @overload
    def set(self, *values: BaseType) -> Expr:
        ...

    @overload
    def set(self: T_tuple, value: ComputedValue[T_tuple]) -> Expr:
        ...

    def set(self, *values):
        if len(values) == 1 and isinstance(values[0], ComputedValue):
            return self._set_with_computed_type(values[0])

        for value in values:
            if not isinstance(value, BaseType):
                raise TealInputError(f"Expected BaseType, got {value}")

        myTypes = self.type_spec().value_type_specs()
        if len(myTypes) != len(values):
            raise TealInputError(
                f"Incorrect length for values. Expected {len(myTypes)}, got {len(values)}"
            )
        if not all(myTypes[i] == values[i].type_spec() for i in range(len(myTypes))):
            raise TealInputError("Input values do not match type")
        return self.stored_value.store(encodeTuple(values))

    def encode(self) -> Expr:
        return self.stored_value.load()

    def length(self) -> Expr:
        """Get the number of values this tuple holds as an Expr."""
        return Int(self.type_spec().length_static())

    def __getitem__(self, index: int) -> "TupleElement":
        if not (0 <= index < self.type_spec().length_static()):
            raise TealInputError(f"Index out of bounds: {index}")
        return TupleElement(self, index)


Tuple.__module__ = "pyteal"

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
        return indexTuple(
            self.tuple.type_spec().value_type_specs(),
            self.tuple.encode(),
            self.index,
            output,
        )


TupleElement.__module__ = "pyteal"

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


Tuple0.__module__ = "pyteal"

T1 = TypeVar("T1", bound=BaseType)


class Tuple1(Tuple, Generic[T1]):
    """A Tuple with 1 value."""

    def __init__(self, value_type_spec: TupleTypeSpec) -> None:
        _tuple_raise_arg_mismatch(1, value_type_spec)
        super().__init__(value_type_spec)


Tuple1.__module__ = "pyteal"

T2 = TypeVar("T2", bound=BaseType)


class Tuple2(Tuple, Generic[T1, T2]):
    """A Tuple with 2 values."""

    def __init__(self, value_type_spec: TupleTypeSpec) -> None:
        _tuple_raise_arg_mismatch(2, value_type_spec)
        super().__init__(value_type_spec)


Tuple2.__module__ = "pyteal"

T3 = TypeVar("T3", bound=BaseType)


class Tuple3(Tuple, Generic[T1, T2, T3]):
    """A Tuple with 3 values."""

    def __init__(
        self,
        value_type_spec: TupleTypeSpec,
    ) -> None:
        _tuple_raise_arg_mismatch(3, value_type_spec)
        super().__init__(value_type_spec)


Tuple3.__module__ = "pyteal"

T4 = TypeVar("T4", bound=BaseType)


class Tuple4(Tuple, Generic[T1, T2, T3, T4]):
    """A Tuple with 4 values."""

    def __init__(
        self,
        value_type_spec: TupleTypeSpec,
    ) -> None:
        _tuple_raise_arg_mismatch(4, value_type_spec)
        super().__init__(value_type_spec)


Tuple4.__module__ = "pyteal"

T5 = TypeVar("T5", bound=BaseType)


class Tuple5(Tuple, Generic[T1, T2, T3, T4, T5]):
    """A Tuple with 5 values."""

    def __init__(
        self,
        value_type_spec: TupleTypeSpec,
    ) -> None:
        _tuple_raise_arg_mismatch(5, value_type_spec)
        super().__init__(value_type_spec)


Tuple5.__module__ = "pyteal"
