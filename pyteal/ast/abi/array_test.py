from typing import List, cast
import pytest

from ... import *
from .type import substringForDecoding
from .tuple import encodeTuple
from .bool import boolSequenceLength
from .array import ArrayElement

# this is not necessary but mypy complains if it's not included
from ... import CompileOptions

options = CompileOptions(version=5)

STATIC_TYPES: List[abi.Type] = [
    abi.Bool(),
    abi.Uint8(),
    abi.Uint16(),
    abi.Uint32(),
    abi.Uint64(),
    abi.Tuple(),
    abi.Tuple(abi.Bool(), abi.Bool(), abi.Uint64()),
    abi.StaticArray(abi.Bool(), 10),
    abi.StaticArray(abi.Uint8(), 10),
    abi.StaticArray(abi.Uint16(), 10),
    abi.StaticArray(abi.Uint32(), 10),
    abi.StaticArray(abi.Uint64(), 10),
    abi.StaticArray(abi.Tuple(abi.Bool(), abi.Bool(), abi.Uint64()), 10),
]

DYNAMIC_TYPES: List[abi.Type] = [
    abi.DynamicArray(abi.Bool()),
    abi.DynamicArray(abi.Uint8()),
    abi.DynamicArray(abi.Uint16()),
    abi.DynamicArray(abi.Uint32()),
    abi.DynamicArray(abi.Uint64()),
    abi.DynamicArray(abi.Tuple()),
    abi.DynamicArray(abi.Tuple(abi.Bool(), abi.Bool(), abi.Uint64())),
    abi.DynamicArray(abi.StaticArray(abi.Bool(), 10)),
    abi.DynamicArray(abi.StaticArray(abi.Uint8(), 10)),
    abi.DynamicArray(abi.StaticArray(abi.Uint16(), 10)),
    abi.DynamicArray(abi.StaticArray(abi.Uint32(), 10)),
    abi.DynamicArray(abi.StaticArray(abi.Uint64(), 10)),
    abi.DynamicArray(
        abi.StaticArray(abi.Tuple(abi.Bool(), abi.Bool(), abi.Uint64()), 10)
    ),
]


def test_StaticArray_init():
    for elementType in STATIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray(elementType, length)
            assert staticArrayType._valueType is elementType
            assert not staticArrayType._has_offsets
            assert staticArrayType._stride == elementType.byte_length_static()
            assert staticArrayType._static_length == length

    for elementType in DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray(elementType, length)
            assert staticArrayType._valueType is elementType
            assert staticArrayType._has_offsets
            assert staticArrayType._stride == 2
            assert staticArrayType._static_length == length


def test_StaticArray_str():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray(elementType, length)
            assert str(staticArrayType) == "{}[{}]".format(elementType, length)


def test_StaticArray_new_instance():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray(elementType, length)
            newInstance = staticArrayType.new_instance()
            assert type(newInstance) is abi.StaticArray
            assert newInstance._valueType is elementType
            assert newInstance._has_offsets == staticArrayType._has_offsets
            assert newInstance._stride == staticArrayType._stride
            assert newInstance._static_length == length


def test_StaticArray_has_same_type_as():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray(elementType, length)
            assert staticArrayType.has_same_type_as(staticArrayType)
            assert not staticArrayType.has_same_type_as(
                abi.StaticArray(elementType, length + 1)
            )
            assert not staticArrayType.has_same_type_as(
                abi.StaticArray(abi.Tuple(elementType), length)
            )


def test_StaticArray_is_dynamic():
    for elementType in STATIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray(elementType, length)
            assert not staticArrayType.is_dynamic()

    for elementType in DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray(elementType, length)
            assert staticArrayType.is_dynamic()


def test_StaticArray_byte_length_static():
    for elementType in STATIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray(elementType, length)
            actual = staticArrayType.byte_length_static()

            if type(elementType) is abi.Bool:
                expected = boolSequenceLength(length)
            else:
                expected = elementType.byte_length_static() * length

            assert actual == expected

    for elementType in DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray(elementType, length)
            with pytest.raises(ValueError):
                staticArrayType.byte_length_static()


def test_StaticArray_decode():
    staticArrayType = abi.StaticArray(abi.Uint64(), 10)
    for startIndex in (None, Int(1)):
        for endIndex in (None, Int(2)):
            for length in (None, Int(3)):
                encoded = Bytes("encoded")

                if endIndex is not None and length is not None:
                    with pytest.raises(TealInputError):
                        staticArrayType.decode(
                            encoded,
                            startIndex=startIndex,
                            endIndex=endIndex,
                            length=length,
                        )
                    continue

                expr = staticArrayType.decode(
                    encoded, startIndex=startIndex, endIndex=endIndex, length=length
                )
                assert expr.type_of() == TealType.none
                assert not expr.has_return()

                expectedExpr = staticArrayType.stored_value.store(
                    substringForDecoding(
                        encoded, startIndex=startIndex, endIndex=endIndex, length=length
                    )
                )
                expected, _ = expectedExpr.__teal__(options)
                expected.addIncoming()
                expected = TealBlock.NormalizeBlocks(expected)

                actual, _ = expr.__teal__(options)
                actual.addIncoming()
                actual = TealBlock.NormalizeBlocks(actual)

                with TealComponent.Context.ignoreExprEquality():
                    assert actual == expected


def test_StaticArray_set():
    staticArrayType = abi.StaticArray(abi.Uint64(), 10)

    with pytest.raises(TealInputError):
        staticArrayType.set([])

    with pytest.raises(TealInputError):
        staticArrayType.set([abi.Uint64()] * 9)

    with pytest.raises(TealInputError):
        staticArrayType.set([abi.Uint64()] * 11)

    with pytest.raises(TealInputError):
        staticArrayType.set([abi.Uint16()] * 10)

    with pytest.raises(TealInputError):
        staticArrayType.set([abi.Uint64()] * 9 + [abi.Uint16()])

    values = [abi.Uint64() for _ in range(10)]
    expr = staticArrayType.set(values)
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expectedExpr = staticArrayType.stored_value.store(encodeTuple(values))
    expected, _ = expectedExpr.__teal__(options)
    expected.addIncoming()
    expected = TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_StaticArray_encode():
    staticArrayType = abi.StaticArray(abi.Uint64(), 10)
    expr = staticArrayType.encode()
    assert expr.type_of() == TealType.bytes
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [TealOp(None, Op.load, staticArrayType.stored_value.slot)]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_StaticArray_length_static():
    for length in (0, 1, 2, 3, 1000):
        staticArrayType = abi.StaticArray(abi.Uint64(), length)
        assert staticArrayType.length_static() == length


def test_StaticArray_length():
    for length in (0, 1, 2, 3, 1000):
        staticArrayType = abi.StaticArray(abi.Uint64(), length)
        expr = staticArrayType.length()
        assert expr.type_of() == TealType.uint64
        assert not expr.has_return()

        expected = TealSimpleBlock([TealOp(None, Op.int, length)])

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_StaticArray_getitem():
    for length in (0, 1, 2, 3, 1000):
        staticArrayType = abi.StaticArray(abi.Uint64(), length)

        for index in range(length):
            # dynamic indexes
            indexExpr = Int(index)
            element = staticArrayType[indexExpr]
            assert type(element) is ArrayElement
            assert element.array is staticArrayType
            assert element.index is indexExpr
            assert element.length is None

        for index in range(length):
            # static indexes
            element = staticArrayType[index]
            assert type(element) is ArrayElement
            assert element.array is staticArrayType
            assert type(element.index) is Int
            assert element.index.value == index
            assert element.length is None

        with pytest.raises(TealInputError):
            staticArrayType[-1]

        with pytest.raises(TealInputError):
            staticArrayType[length]


def test_DynamicArray_init():
    for elementType in STATIC_TYPES:
        dynamicArrayType = abi.DynamicArray(elementType)
        assert dynamicArrayType._valueType is elementType
        assert not dynamicArrayType._has_offsets
        assert dynamicArrayType._stride == elementType.byte_length_static()
        assert dynamicArrayType._static_length is None

    for elementType in DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray(elementType)
        assert dynamicArrayType._valueType is elementType
        assert dynamicArrayType._has_offsets
        assert dynamicArrayType._stride == 2
        assert dynamicArrayType._static_length is None


def test_DynamicArray_str():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray(elementType)
        assert str(dynamicArrayType) == "{}[]".format(elementType)


def test_DynamicArray_new_instance():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray(elementType)
        newInstance = dynamicArrayType.new_instance()
        assert type(newInstance) is abi.DynamicArray
        assert newInstance._valueType is elementType
        assert newInstance._has_offsets == dynamicArrayType._has_offsets
        assert newInstance._stride == dynamicArrayType._stride
        assert newInstance._static_length is None


def test_DynamicArray_has_same_type_as():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray(elementType)
        assert dynamicArrayType.has_same_type_as(dynamicArrayType)
        assert not dynamicArrayType.has_same_type_as(
            abi.DynamicArray(abi.Tuple(elementType))
        )


def test_DynamicArray_is_dynamic():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray(elementType)
        assert dynamicArrayType.is_dynamic()


def test_DynamicArray_byte_length_static():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray(elementType)
        with pytest.raises(ValueError):
            dynamicArrayType.byte_length_static()


def test_DynamicArray_decode():
    dynamicArrayType = abi.DynamicArray(abi.Uint64())
    for startIndex in (None, Int(1)):
        for endIndex in (None, Int(2)):
            for length in (None, Int(3)):
                encoded = Bytes("encoded")

                if endIndex is not None and length is not None:
                    with pytest.raises(TealInputError):
                        dynamicArrayType.decode(
                            encoded,
                            startIndex=startIndex,
                            endIndex=endIndex,
                            length=length,
                        )
                    continue

                expr = dynamicArrayType.decode(
                    encoded, startIndex=startIndex, endIndex=endIndex, length=length
                )
                assert expr.type_of() == TealType.none
                assert not expr.has_return()

                expectedExpr = dynamicArrayType.stored_value.store(
                    substringForDecoding(
                        encoded, startIndex=startIndex, endIndex=endIndex, length=length
                    )
                )
                expected, _ = expectedExpr.__teal__(options)
                expected.addIncoming()
                expected = TealBlock.NormalizeBlocks(expected)

                actual, _ = expr.__teal__(options)
                actual.addIncoming()
                actual = TealBlock.NormalizeBlocks(actual)

                with TealComponent.Context.ignoreExprEquality():
                    assert actual == expected


def test_DynamicArray_set():
    dynamicArrayType = abi.DynamicArray(abi.Uint64())

    valuesToSet: List[abi.Uint64] = [
        [],
        [abi.Uint64()],
        [abi.Uint64() for _ in range(10)],
    ]

    for values in valuesToSet:
        expr = dynamicArrayType.set(values)
        assert expr.type_of() == TealType.none
        assert not expr.has_return()

        length_tmp = abi.Uint16()
        expectedExpr = dynamicArrayType.stored_value.store(
            Concat(
                Seq(length_tmp.set(len(values)), length_tmp.encode()),
                encodeTuple(values),
            )
        )
        expected, _ = expectedExpr.__teal__(options)
        expected.addIncoming()
        expected = TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            with TealComponent.Context.ignoreScratchSlotEquality():
                assert actual == expected

        assert TealBlock.MatchScratchSlotReferences(
            TealBlock.GetReferencedScratchSlots(actual),
            TealBlock.GetReferencedScratchSlots(expected),
        )


def test_DynamicArray_encode():
    dynamicArrayType = abi.DynamicArray(abi.Uint64())
    expr = dynamicArrayType.encode()
    assert expr.type_of() == TealType.bytes
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [TealOp(None, Op.load, dynamicArrayType.stored_value.slot)]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_DynamicArray_length():
    dynamicArrayType = abi.DynamicArray(abi.Uint64())
    expr = dynamicArrayType.length()
    assert expr.type_of() == TealType.uint64
    assert not expr.has_return()

    length_tmp = abi.Uint16()
    expectedExpr = Seq(length_tmp.decode(dynamicArrayType.encode()), length_tmp.get())
    expected, _ = expectedExpr.__teal__(options)
    expected.addIncoming()
    expected = TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        with TealComponent.Context.ignoreScratchSlotEquality():
            assert actual == expected

    assert TealBlock.MatchScratchSlotReferences(
        TealBlock.GetReferencedScratchSlots(actual),
        TealBlock.GetReferencedScratchSlots(expected),
    )


def test_DynamicArray_getitem():
    dynamicArrayType = abi.DynamicArray(abi.Uint64())

    for index in (0, 1, 2, 3, 1000):
        # dynamic indexes
        indexExpr = Int(index)
        element = dynamicArrayType[indexExpr]
        assert type(element) is ArrayElement
        assert element.array is dynamicArrayType
        assert element.index is indexExpr
        assert element.length is None

    for index in (0, 1, 2, 3, 1000):
        # static indexes
        element = dynamicArrayType[index]
        assert type(element) is ArrayElement
        assert element.array is dynamicArrayType
        assert type(element.index) is Int
        assert element.index.value == index
        assert element.length is None

    with pytest.raises(TealInputError):
        dynamicArrayType[-1]


def test_ArrayElement_store_into():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        staticArrayType = abi.StaticArray(elementType, 100)
        index = Int(9)

        for lengthExpr in (None, Int(500)):
            element = ArrayElement(staticArrayType, index, lengthExpr)
            output = elementType.new_instance()
            expr = element.store_into(output)

            encoded = staticArrayType.encode()
            stride = Int(staticArrayType._stride)
            expectedLength = (
                lengthExpr if lengthExpr is not None else staticArrayType.length()
            )
            if type(elementType) is abi.Bool:
                expectedExpr = cast(abi.Bool, output).decodeBit(encoded, index)
            elif not elementType.is_dynamic():
                expectedExpr = output.decode(
                    encoded, startIndex=stride * index, length=stride
                )
            else:
                expectedExpr = output.decode(
                    encoded,
                    startIndex=ExtractUint16(encoded, stride * index),
                    endIndex=If(index + Int(1) == expectedLength)
                    .Then(expectedLength * stride)
                    .Else(ExtractUint16(encoded, stride * index + Int(2))),
                )

            expected, _ = expectedExpr.__teal__(options)
            expected.addIncoming()
            expected = TealBlock.NormalizeBlocks(expected)

            actual, _ = expr.__teal__(options)
            actual.addIncoming()
            actual = TealBlock.NormalizeBlocks(actual)

            with TealComponent.Context.ignoreExprEquality():
                assert actual == expected

            with pytest.raises(TealInputError):
                element.store_into(abi.Tuple(output))

    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray(elementType)
        index = Int(9)

        for lengthExpr in (None, Int(500)):
            element = ArrayElement(dynamicArrayType, index, lengthExpr)
            output = elementType.new_instance()
            expr = element.store_into(output)

            encoded = dynamicArrayType.encode()
            stride = Int(dynamicArrayType._stride)
            expectedLength = (
                lengthExpr if lengthExpr is not None else dynamicArrayType.length()
            )
            if type(elementType) is abi.Bool:
                expectedExpr = cast(abi.Bool, output).decodeBit(
                    encoded, index + Int(16)
                )
            elif not elementType.is_dynamic():
                expectedExpr = output.decode(
                    encoded, startIndex=stride * index + Int(2), length=stride
                )
            else:
                expectedExpr = output.decode(
                    encoded,
                    startIndex=ExtractUint16(encoded, stride * index + Int(2)) + Int(2),
                    endIndex=If(index + Int(1) == expectedLength)
                    .Then(expectedLength * stride)
                    .Else(ExtractUint16(encoded, stride * index + Int(2) + Int(2)))
                    + Int(2),
                )

            expected, _ = expectedExpr.__teal__(options)
            expected.addIncoming()
            expected = TealBlock.NormalizeBlocks(expected)

            actual, _ = expr.__teal__(options)
            actual.addIncoming()
            actual = TealBlock.NormalizeBlocks(actual)

            with TealComponent.Context.ignoreExprEquality():
                with TealComponent.Context.ignoreScratchSlotEquality():
                    assert actual == expected

            assert TealBlock.MatchScratchSlotReferences(
                TealBlock.GetReferencedScratchSlots(actual),
                TealBlock.GetReferencedScratchSlots(expected),
            )

            with pytest.raises(TealInputError):
                element.store_into(abi.Tuple(output))
