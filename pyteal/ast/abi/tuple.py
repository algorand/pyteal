from abc import abstractmethod
from typing import List, Sequence, Dict, cast, Type as PyType, Tuple as PyTuple, Union

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

from .type import Type, ComputedType, substringForDecoding
from .bool import (
    Bool,
    consecutiveBoolNum,
    boolSequenceLength,
    encodeBoolSequence,
    boolAwareStaticByteLength,
)
from .uint import NUM_BITS_IN_BYTE, Uint16


def encodeTuple(values: Sequence[Type]) -> Expr:
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

        if elem.is_dynamic():
            head_length_static += 2
            dynamicValueIndexToHeadIndex[i] = len(heads)
            heads.append(Seq())  # a placeholder
            continue

        head_length_static += elem.byte_length_static()
        heads.append(elem.encode())

    tail_offset = Uint16()
    tail_offset_accumulator = Uint16()
    tail_holder = ScratchVar(TealType.bytes)
    encoded_tail = ScratchVar(TealType.bytes)

    firstDynamicTail = True
    for i, elem in enumerate(values):
        if elem.is_dynamic():
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
                [nextValue.is_dynamic() for nextValue in values[i + 1 :]]
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
    valueTypes: Sequence[Type], encoded: Expr, index: int, output: Type
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

        if type(typeBefore) is Bool:
            lastBoolStart = offset
            lastBoolLength = consecutiveBoolNum(valueTypes, i)
            offset += boolSequenceLength(lastBoolLength)
            ignoreNext = lastBoolLength - 1
            continue

        if typeBefore.is_dynamic():
            offset += 2
            continue

        offset += typeBefore.byte_length_static()

    valueType = valueTypes[index]
    if not valueType.has_same_type_as(output):
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

            if type(typeAfter) is Bool:
                boolLength = consecutiveBoolNum(valueTypes, i)
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


class Tuple(Type):
    @classmethod
    def of(cls, *params: PyType[Type]) -> PyType["Tuple"]:
        """Get an instance of an instantiable Tuple class that can hold the given types.

        Args:
            params: A list of instantiable Type classes that the returned Tuple class should hold.
                The order of these parameters will be the same order of the Tuple's types.

        Returns:
            An instantiable Tuple class that holds the given types.
        """
        # TODO: give a better error message if the below condition is not true
        assert all(issubclass(param, Type) for param in params)

        # TODO: verify all params are instantiable. It should not be possible to call Tuple.of(Type)

        class TypedTuple(Tuple):
            def __class_getitem__(cls, _):
                # prevent Tuple[A][B]
                raise TypeError("Cannot index into Tuple[...]")

            @classmethod
            def value_types(cls) -> List[PyType[Type]]:
                return list(params)

        return TypedTuple

    def __class_getitem__(cls, params: PyTuple[PyType[Type], ...]) -> PyType["Tuple"]:
        """Syntactic sugar for the Tuple.of function.

        This special function is called when the Tuple type is indexed, e.g. `Tuple[A, B, C]`.
        """
        return cls.of(*params)

    @classmethod
    def has_same_type_as(cls, other: Union[PyType[Type], Type]) -> bool:
        if not issubclass(other, Tuple) and not isinstance(other, Tuple):
            return False

        myValueTypes = cls.value_types()
        otherValueTypes = other.value_types()

        return len(myValueTypes) == len(otherValueTypes) and all(
            myValueTypes[i].has_same_type_as(otherValueTypes[i])
            for i in range(len(myValueTypes))
        )

    @classmethod
    def is_dynamic(cls) -> bool:
        return any(valueType.is_dynamic() for valueType in cls.value_types())

    @classmethod
    def byte_length_static(cls) -> int:
        if cls.is_dynamic():
            raise ValueError("Type is dynamic")
        return boolAwareStaticByteLength(cls.value_types())

    @classmethod
    def storage_type(cls) -> TealType:
        return TealType.bytes

    @classmethod
    def __str__(cls) -> str:
        return "({})".format(",".join(map(lambda x: x.__str__(), cls.value_types())))

    @classmethod
    @abstractmethod
    def value_types(cls) -> List[PyType[Type]]:
        """Get a list of the types of values this tuple holds."""
        pass

    @classmethod
    def length_static(cls) -> int:
        """Get the number of values this tuple holds."""
        return len(cls.value_types())

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

    def set(self, *values: Type) -> Expr:
        myTypes = self.value_types()
        if len(myTypes) != len(values):
            raise TealInputError(
                "Incorrect length for values. Expected {}, got {}".format(
                    len(myTypes), len(values)
                )
            )
        if not all(myTypes[i].has_same_type_as(values[i]) for i in range(len(myTypes))):
            raise TealInputError("Input values do not match type")
        return self.stored_value.store(encodeTuple(values))

    def encode(self) -> Expr:
        return self.stored_value.load()

    def length(self) -> Expr:
        """Get the number of values this tuple holds as an Expr."""
        return Int(self.length_static())

    def __getitem__(self, index: int) -> "TupleElement":
        if not (0 <= index < self.length_static()):
            raise TealInputError("Index out of bounds")
        valueType = self.value_types()[index]
        return TupleElement[valueType](index)


Tuple.__module__ = "pyteal"


class TupleElement(ComputedType[Type]):
    """Represents the extraction of a specific element from a Tuple."""

    def __init__(self, tuple: Tuple, index: int) -> None:
        super().__init__()
        self.tuple = tuple
        self.index = index

    def produced_type(self) -> PyType[Type]:
        return self.tuple.value_types()[self.index]

    def store_into(self, output: Type) -> Expr:
        return indexTuple(
            self.tuple.value_types(), self.tuple.encode(), self.index, output
        )


TupleElement.__module__ = "pyteal"
