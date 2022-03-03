from typing import List, Type, Literal as L, cast
import pytest

from ... import *
from .type import substringForDecoding
from .tuple import encodeTuple
from .bool import boolSequenceLength
from .array import ArrayElement

# this is not necessary but mypy complains if it's not included
from ... import CompileOptions

options = CompileOptions(version=5)

STATIC_TYPES: List[Type[abi.Type]] = [
    abi.Bool,
    abi.Uint8,
    abi.Uint16,
    abi.Uint32,
    abi.Uint64,
    abi.Tuple.of(),
    abi.Tuple[abi.Bool, abi.Bool, abi.Uint64],
    abi.StaticArray[abi.Bool, L[10]],
    abi.StaticArray[abi.Uint8, L[10]],
    abi.StaticArray[abi.Uint16, L[10]],
    abi.StaticArray[abi.Uint32, L[10]],
    abi.StaticArray[abi.Uint64, L[10]],
    abi.StaticArray[abi.Tuple[abi.Bool, abi.Bool, abi.Uint64], L[10]],
]

DYNAMIC_TYPES: List[Type[abi.Type]] = [
    abi.DynamicArray[abi.Bool],
    abi.DynamicArray[abi.Uint8],
    abi.DynamicArray[abi.Uint16],
    abi.DynamicArray[abi.Uint32],
    abi.DynamicArray[abi.Uint64],
    abi.DynamicArray[abi.Tuple.of()],
    abi.DynamicArray[abi.Tuple[abi.Bool, abi.Bool, abi.Uint64]],
    abi.DynamicArray[abi.StaticArray[abi.Bool, L[10]]],
    abi.DynamicArray[abi.StaticArray[abi.Uint8, L[10]]],
    abi.DynamicArray[abi.StaticArray[abi.Uint16, L[10]]],
    abi.DynamicArray[abi.StaticArray[abi.Uint32, L[10]]],
    abi.DynamicArray[abi.StaticArray[abi.Uint64, L[10]]],
    abi.DynamicArray[abi.StaticArray[abi.Tuple[abi.Bool, abi.Bool, abi.Uint64], L[10]]],
]


def test_StaticArray_init():
    for elementType in STATIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray[elementType, length]
            assert staticArrayType.value_type() is elementType
            assert not staticArrayType.is_length_dynamic()
            assert staticArrayType._stride() == elementType.byte_length_static()
            assert staticArrayType.length_static() == length

        with pytest.raises(TypeError):
            abi.StaticArray[elementType, -1]

    for elementType in DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray[elementType, length]
            assert staticArrayType.value_type() is elementType
            assert not staticArrayType.is_length_dynamic()
            assert staticArrayType._stride() == 2
            assert staticArrayType.length_static() == length

        with pytest.raises(TypeError):
            abi.StaticArray[elementType, -1]


def test_StaticArray_str():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray[elementType, length]
            assert str(staticArrayType()) == "{}[{}]".format(
                elementType.__str__(), length
            )


def test_StaticArray_new_instance():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        for length in range(256):
            abi.StaticArray[elementType, length]()

        value_with_literal = abi.StaticArray[elementType, L[10]]()
        assert value_with_literal.length_static() == 10


def test_StaticArray_has_same_type_as():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        for length in range(10):
            # lowered the range here because isinstance and issubclass have relatively poor
            # performance possibly due to dynamically creating classes at runtime
            staticArrayType = abi.StaticArray[elementType, length]
            assert staticArrayType.has_same_type_as(staticArrayType)
            assert staticArrayType.has_same_type_as(staticArrayType())

            assert not staticArrayType.has_same_type_as(
                abi.StaticArray[elementType, length + 1]
            )
            assert not staticArrayType.has_same_type_as(
                abi.StaticArray[elementType, length + 1]()
            )

            assert not staticArrayType.has_same_type_as(
                abi.StaticArray[abi.Tuple[elementType], length]
            )
            assert not staticArrayType.has_same_type_as(
                abi.StaticArray[abi.Tuple[elementType], length]()
            )


def test_StaticArray_is_dynamic():
    for elementType in STATIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray[elementType, length]
            assert not staticArrayType.is_dynamic()

    for elementType in DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray[elementType, length]
            assert staticArrayType.is_dynamic()


def test_StaticArray_byte_length_static():
    for elementType in STATIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray[elementType, length]
            actual = staticArrayType.byte_length_static()

            if elementType is abi.Bool:
                expected = boolSequenceLength(length)
            else:
                expected = elementType.byte_length_static() * length

            assert actual == expected

    for elementType in DYNAMIC_TYPES:
        for length in range(256):
            staticArrayType = abi.StaticArray[elementType, length]
            with pytest.raises(ValueError):
                staticArrayType.byte_length_static()


def test_StaticArray_decode():
    encoded = Bytes("encoded")
    for startIndex in (None, Int(1)):
        for endIndex in (None, Int(2)):
            for length in (None, Int(3)):
                value = abi.StaticArray[abi.Uint64, 10]()

                if endIndex is not None and length is not None:
                    with pytest.raises(TealInputError):
                        value.decode(
                            encoded,
                            startIndex=startIndex,
                            endIndex=endIndex,
                            length=length,
                        )
                    continue

                expr = value.decode(
                    encoded, startIndex=startIndex, endIndex=endIndex, length=length
                )
                assert expr.type_of() == TealType.none
                assert not expr.has_return()

                expectedExpr = value.stored_value.store(
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


def test_StaticArray_set_values():
    value = abi.StaticArray[abi.Uint64, 10]()

    with pytest.raises(TealInputError):
        value.set([])

    with pytest.raises(TealInputError):
        value.set([abi.Uint64()] * 9)

    with pytest.raises(TealInputError):
        value.set([abi.Uint64()] * 11)

    with pytest.raises(TealInputError):
        value.set([abi.Uint16()] * 10)

    with pytest.raises(TealInputError):
        value.set([abi.Uint64()] * 9 + [abi.Uint16()])

    values = [abi.Uint64() for _ in range(10)]
    expr = value.set(values)
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expectedExpr = value.stored_value.store(encodeTuple(values))
    expected, _ = expectedExpr.__teal__(options)
    expected.addIncoming()
    expected = TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_StaticArray_set_copy():
    value = abi.StaticArray[abi.Uint64, 10]()
    otherArray = abi.StaticArray[abi.Uint64, 10]()

    with pytest.raises(TealInputError):
        value.set(abi.StaticArray[abi.Uint64, 11]())

    with pytest.raises(TealInputError):
        value.set(abi.StaticArray[abi.Uint8, 10]())

    with pytest.raises(TealInputError):
        value.set(abi.Uint64())

    expr = value.set(otherArray)
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.load, otherArray.stored_value.slot),
            TealOp(None, Op.store, value.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_StaticArray_encode():
    value = abi.StaticArray[abi.Uint64, 10]()
    expr = value.encode()
    assert expr.type_of() == TealType.bytes
    assert not expr.has_return()

    expected = TealSimpleBlock([TealOp(None, Op.load, value.stored_value.slot)])

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_StaticArray_length_static():
    for length in (0, 1, 2, 3, 1000):
        staticArrayType = abi.StaticArray[abi.Uint64, length]
        assert staticArrayType.length_static() == length


def test_StaticArray_length():
    for length in (0, 1, 2, 3, 1000):
        value = abi.StaticArray[abi.Uint64, length]()
        expr = value.length()
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
        value = abi.StaticArray[abi.Uint64, length]()

        for index in range(length):
            # dynamic indexes
            indexExpr = Int(index)
            element = value[indexExpr]
            assert type(element) is ArrayElement
            assert element.array is value
            assert element.index is indexExpr

        for index in range(length):
            # static indexes
            element = value[index]
            assert type(element) is ArrayElement
            assert element.array is value
            assert type(element.index) is Int
            assert element.index.value == index

        with pytest.raises(TealInputError):
            value[-1]

        with pytest.raises(TealInputError):
            value[length]


def test_DynamicArray_init():
    for elementType in STATIC_TYPES:
        dynamicArrayType = abi.DynamicArray[elementType]
        assert dynamicArrayType.value_type() is elementType
        assert dynamicArrayType.is_length_dynamic()
        assert dynamicArrayType._stride() == elementType.byte_length_static()

    for elementType in DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray[elementType]
        assert dynamicArrayType.value_type() is elementType
        assert dynamicArrayType.is_length_dynamic()
        assert dynamicArrayType._stride() == 2


def test_DynamicArray_str():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray[elementType]
        assert str(dynamicArrayType()) == "{}[]".format(elementType.__str__())


def test_DynamicArray_new_instance():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        abi.DynamicArray[elementType]()


def test_DynamicArray_has_same_type_as():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray[elementType]

        assert dynamicArrayType.has_same_type_as(dynamicArrayType)
        assert dynamicArrayType.has_same_type_as(dynamicArrayType())

        assert not dynamicArrayType.has_same_type_as(
            abi.DynamicArray[abi.Tuple[elementType]]
        )
        assert not dynamicArrayType.has_same_type_as(
            abi.DynamicArray[abi.Tuple[elementType]]()
        )


def test_DynamicArray_is_dynamic():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray[elementType]
        assert dynamicArrayType.is_dynamic()


def test_DynamicArray_byte_length_static():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArrayType = abi.DynamicArray[elementType]
        with pytest.raises(ValueError):
            dynamicArrayType.byte_length_static()


def test_DynamicArray_decode():
    encoded = Bytes("encoded")
    for startIndex in (None, Int(1)):
        for endIndex in (None, Int(2)):
            for length in (None, Int(3)):
                value = abi.DynamicArray[abi.Uint64]()

                if endIndex is not None and length is not None:
                    with pytest.raises(TealInputError):
                        value.decode(
                            encoded,
                            startIndex=startIndex,
                            endIndex=endIndex,
                            length=length,
                        )
                    continue

                expr = value.decode(
                    encoded, startIndex=startIndex, endIndex=endIndex, length=length
                )
                assert expr.type_of() == TealType.none
                assert not expr.has_return()

                expectedExpr = value.stored_value.store(
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


def test_DynamicArray_set_values():
    valuesToSet: List[abi.Uint64] = [
        [],
        [abi.Uint64()],
        [abi.Uint64() for _ in range(10)],
    ]

    for values in valuesToSet:
        value = abi.DynamicArray[abi.Uint64]()
        expr = value.set(values)
        assert expr.type_of() == TealType.none
        assert not expr.has_return()

        length_tmp = abi.Uint16()
        expectedExpr = value.stored_value.store(
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


def test_DynamicArray_set_copy():
    value = abi.DynamicArray[abi.Uint64]()
    otherArray = abi.DynamicArray[abi.Uint64]()

    with pytest.raises(TealInputError):
        value.set(abi.DynamicArray[abi.Uint8]())

    with pytest.raises(TealInputError):
        value.set(abi.Uint64())

    expr = value.set(otherArray)
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.load, otherArray.stored_value.slot),
            TealOp(None, Op.store, value.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_DynamicArray_encode():
    value = abi.DynamicArray[abi.Uint64]()
    expr = value.encode()
    assert expr.type_of() == TealType.bytes
    assert not expr.has_return()

    expected = TealSimpleBlock([TealOp(None, Op.load, value.stored_value.slot)])

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_DynamicArray_length():
    value = abi.DynamicArray[abi.Uint64]()
    expr = value.length()
    assert expr.type_of() == TealType.uint64
    assert not expr.has_return()

    length_tmp = abi.Uint16()
    expectedExpr = Seq(length_tmp.decode(value.encode()), length_tmp.get())
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
    value = abi.DynamicArray[abi.Uint64]()

    for index in (0, 1, 2, 3, 1000):
        # dynamic indexes
        indexExpr = Int(index)
        element = value[indexExpr]
        assert type(element) is ArrayElement
        assert element.array is value
        assert element.index is indexExpr

    for index in (0, 1, 2, 3, 1000):
        # static indexes
        element = value[index]
        assert type(element) is ArrayElement
        assert element.array is value
        assert type(element.index) is Int
        assert element.index.value == index

    with pytest.raises(TealInputError):
        value[-1]


def test_ArrayElement_init():
    array = abi.DynamicArray[abi.Uint64]()
    index = Int(6)

    element = ArrayElement(array, index)
    assert element.array is array
    assert element.index is index

    with pytest.raises(TealTypeError):
        ArrayElement(array, Bytes("abc"))

    with pytest.raises(TealTypeError):
        ArrayElement(array, Assert(index))


def test_ArrayElement_store_into():
    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        staticArray = abi.StaticArray[elementType, 100]()
        index = Int(9)

        element = ArrayElement(staticArray, index)
        output = elementType()
        expr = element.store_into(output)

        encoded = staticArray.encode()
        stride = Int(staticArray._stride())
        expectedLength = staticArray.length()
        if elementType is abi.Bool:
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
                .Then(Len(encoded))
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
            element.store_into(abi.Tuple[elementType]())

    for elementType in STATIC_TYPES + DYNAMIC_TYPES:
        dynamicArray = abi.DynamicArray[elementType]()
        index = Int(9)

        element = ArrayElement(dynamicArray, index)
        output = elementType()
        expr = element.store_into(output)

        encoded = dynamicArray.encode()
        stride = Int(dynamicArray._stride())
        expectedLength = dynamicArray.length()
        if elementType is abi.Bool:
            expectedExpr = cast(abi.Bool, output).decodeBit(encoded, index + Int(16))
        elif not elementType.is_dynamic():
            expectedExpr = output.decode(
                encoded, startIndex=stride * index + Int(2), length=stride
            )
        else:
            expectedExpr = output.decode(
                encoded,
                startIndex=ExtractUint16(encoded, stride * index + Int(2)) + Int(2),
                endIndex=If(index + Int(1) == expectedLength)
                .Then(Len(encoded))
                .Else(
                    ExtractUint16(encoded, stride * index + Int(2) + Int(2)) + Int(2)
                ),
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
            element.store_into(abi.Tuple[elementType]())
