from typing import List, Sequence, Dict, Generic, TypeVar, cast

from ...types import TealType
from ...errors import TealInputError
from ..expr import Expr
from ..seq import Seq
from ..int import Int
from ..bytes import Bytes
from ..unaryexpr import Len
from ..binaryexpr import ExtractUint16
from ..naryexpr import Concat
from ..scratchvar import ScratchVar

from .type import TypeSpec, BaseType, ComputedType
from .bool import (
    Bool,
    BoolTypeSpec,
    consecutiveBoolNum,
    consecutiveBoolTypeNum,
    boolSequenceLength,
    encodeBoolSequence,
    boolAwareStaticByteLength,
)
from .uint import NUM_BITS_IN_BYTE, Uint16
from .util import substringForDecoding


def encodeTuple(values: Sequence[BaseType]) -> Expr:
    heads: List[Expr] = []
    head_length_static: int = 0

    dynamicValueIndexToHeadIndex: Dict[int, int] = dict()
    ignoreNext = 0
    for i, elem in enumerate(values):
        if ignoreNext > 0:
            ignoreNext -= 1
            continue

        if type(elem) is Bool:
            numBools = consecutiveBoolNum(values, i)
            ignoreNext = numBools - 1
            head_length_static += boolSequenceLength(numBools)
            heads.append(
                encodeBoolSequence(cast(Sequence[Bool], values[i : i + numBools]))
            )
            continue

        if elem.get_type_spec().is_dynamic():
            head_length_static += 2
            dynamicValueIndexToHeadIndex[i] = len(heads)
            heads.append(Seq())  # a placeholder
            continue

        head_length_static += elem.get_type_spec().byte_length_static()
        heads.append(elem.encode())

    tail_offset = Uint16()
    tail_offset_accumulator = Uint16()
    tail_holder = ScratchVar(TealType.bytes)
    encoded_tail = ScratchVar(TealType.bytes)

    firstDynamicTail = True
    for i, elem in enumerate(values):
        if elem.get_type_spec().is_dynamic():
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
                [
                    nextValue.get_type_spec().is_dynamic()
                    for nextValue in values[i + 1 :]
                ]
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

        if type(typeBefore) is BoolTypeSpec:
            lastBoolStart = offset
            lastBoolLength = consecutiveBoolTypeNum(valueTypes, i)
            offset += boolSequenceLength(lastBoolLength)
            ignoreNext = lastBoolLength - 1
            continue

        if typeBefore.is_dynamic():
            offset += 2
            continue

        offset += typeBefore.byte_length_static()

    valueType = valueTypes[index]
    if output.get_type_spec() != valueType:
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
                boolLength = consecutiveBoolTypeNum(valueTypes, i)
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
            return output.decode(encoded, startIndex=startIndex)

        # There is a dynamic value after this one, and endIndex is where its tail starts, so decode
        # the substring from startIndex to endIndex
        endIndex = ExtractUint16(encoded, Int(nextDynamicValueOffset))
        return output.decode(encoded, startIndex=startIndex, endIndex=endIndex)

    startIndex = Int(offset)
    length = Int(valueType.byte_length_static())

    if index + 1 == len(valueTypes):
        if offset == 0:
            # This is the first and only value in the tuple, so decode all of encoded
            return output.decode(encoded)
        # This is the last value in the tuple, so decode the substring from startIndex to the end of
        # encoded
        return output.decode(encoded, startIndex=startIndex)

    if offset == 0:
        # This is the first value in the tuple, so decode the substring from 0 with length length
        return output.decode(encoded, length=length)

    # This is not the first or last value, so decode the substring from startIndex with length length
    return output.decode(encoded, startIndex=startIndex, length=length)


class TupleTypeSpec(TypeSpec):
    def __init__(self, *value_type_specs: TypeSpec) -> None:
        super().__init__()
        self.value_specs = list(value_type_specs)

    def value_type_specs(self) -> List[TypeSpec]:
        return self.value_specs

    def length_static(self) -> int:
        """Get the number of values this tuple holds."""
        return len(self.value_specs)

    def new_instance(self) -> "Tuple":
        return Tuple(*self.value_specs)

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
        return "({})".format(",".join(map(lambda x: str(x), self.value_type_specs())))


TupleTypeSpec.__module__ = "pyteal"


class Tuple(BaseType):
    def __init__(self, *value_type_specs: TypeSpec) -> None:
        super().__init__(TupleTypeSpec(*value_type_specs))

    def get_type_spec(self) -> TupleTypeSpec:
        return cast(TupleTypeSpec, super().get_type_spec())

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        extracted = substringForDecoding(
            encoded, startIndex=startIndex, endIndex=endIndex, length=length
        )
        return self.stored_value.store(extracted)

    def set(self, *values: BaseType) -> Expr:
        myTypes = self.get_type_spec().value_type_specs()
        if len(myTypes) != len(values):
            raise TealInputError(
                "Incorrect length for values. Expected {}, got {}".format(
                    len(myTypes), len(values)
                )
            )
        if not all(
            myTypes[i] == values[i].get_type_spec() for i in range(len(myTypes))
        ):
            raise TealInputError("Input values do not match type")
        return self.stored_value.store(encodeTuple(values))

    def encode(self) -> Expr:
        return self.stored_value.load()

    def length(self) -> Expr:
        """Get the number of values this tuple holds as an Expr."""
        return Int(self.get_type_spec().length_static())

    def __getitem__(self, index: int) -> "TupleElement":
        if not (0 <= index < self.get_type_spec().length_static()):
            raise TealInputError("Index out of bounds")
        return TupleElement(self, index)


Tuple.__module__ = "pyteal"


class TupleElement(ComputedType[BaseType]):
    """Represents the extraction of a specific element from a Tuple."""

    def __init__(self, tuple: Tuple, index: int) -> None:
        super().__init__()
        self.tuple = tuple
        self.index = index

    def produced_type_spec(self) -> TypeSpec:
        return self.tuple.get_type_spec().value_type_specs()[self.index]

    def store_into(self, output: BaseType) -> Expr:
        return indexTuple(
            self.tuple.get_type_spec().value_type_specs(),
            self.tuple.encode(),
            self.index,
            output,
        )


TupleElement.__module__ = "pyteal"


class Tuple0(Tuple):
    def __init__(self) -> None:
        super().__init__()


Tuple0.__module__ = "pyteal"

T1 = TypeVar("T1", bound=BaseType)


class Tuple1(Tuple, Generic[T1]):
    def __init__(self, value1_type_spec: TypeSpec) -> None:
        super().__init__(value1_type_spec)


Tuple1.__module__ = "pyteal"

T2 = TypeVar("T2", bound=BaseType)


class Tuple2(Tuple, Generic[T1, T2]):
    def __init__(self, value1_type_spec: TypeSpec, value2_type_spec: TypeSpec) -> None:
        super().__init__(value1_type_spec, value2_type_spec)


Tuple2.__module__ = "pyteal"

T3 = TypeVar("T3", bound=BaseType)


class Tuple3(Tuple, Generic[T1, T2, T3]):
    def __init__(
        self,
        value1_type_spec: TypeSpec,
        value2_type_spec: TypeSpec,
        value3_type_spec: TypeSpec,
    ) -> None:
        super().__init__(value1_type_spec, value2_type_spec, value3_type_spec)


Tuple3.__module__ = "pyteal"
