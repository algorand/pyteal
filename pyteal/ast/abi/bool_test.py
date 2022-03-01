from typing import NamedTuple, List
import pytest

from ... import *
from .bool import (
    boolAwareStaticByteLength,
    consecutiveBoolNum,
    boolSequenceLength,
    encodeBoolSequence,
)

# this is not necessary but mypy complains if it's not included
from ... import CompileOptions

options = CompileOptions(version=5)


def test_Bool_str():
    boolType = abi.Bool()
    assert str(boolType) == "bool"


def test_Bool_is_dynamic():
    boolType = abi.Bool()
    assert not boolType.is_dynamic()


def test_Bool_has_same_type_as():
    boolType = abi.Bool()
    assert boolType.has_same_type_as(abi.Bool())

    for otherType in (
        abi.Byte(),
        abi.Uint64(),
        abi.StaticArray(boolType, 1),
        abi.DynamicArray(boolType),
    ):
        assert not boolType.has_same_type_as(otherType)


def test_Bool_new_instance():
    boolType = abi.Bool()
    assert type(boolType.new_instance()) is abi.Bool


def test_Bool_set_static():
    boolType = abi.Bool()
    for value in (True, False):
        expr = boolType.set(value)
        assert expr.type_of() == TealType.none
        assert not expr.has_return()

        expected = TealSimpleBlock(
            [
                TealOp(None, Op.int, 1 if value else 0),
                TealOp(None, Op.store, boolType.stored_value.slot),
            ]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_Bool_set_expr():
    boolType = abi.Bool()
    expr = boolType.set(Int(0).Or(Int(1)))
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.int, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.logic_or),
            TealOp(None, Op.store, boolType.stored_value.slot),
            TealOp(None, Op.load, boolType.stored_value.slot),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.lt),
            TealOp(None, Op.assert_),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Bool_set_copy():
    other = abi.Bool()
    boolType = abi.Bool()
    expr = boolType.set(other)
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.load, other.stored_value.slot),
            TealOp(None, Op.store, boolType.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Bool_get():
    boolType = abi.Bool()
    expr = boolType.get()
    assert expr.type_of() == TealType.uint64
    assert not expr.has_return()

    expected = TealSimpleBlock([TealOp(expr, Op.load, boolType.stored_value.slot)])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_Bool_decode():
    boolType = abi.Bool()
    encoded = Bytes("encoded")
    for startIndex in (None, Int(1)):
        for endIndex in (None, Int(2)):
            for length in (None, Int(3)):
                expr = boolType.decode(
                    encoded, startIndex=startIndex, endIndex=endIndex, length=length
                )
                assert expr.type_of() == TealType.none
                assert not expr.has_return()

                expected = TealSimpleBlock(
                    [
                        TealOp(None, Op.byte, '"encoded"'),
                        TealOp(None, Op.int, 0 if startIndex is None else 1),
                        TealOp(None, Op.int, 8),
                        TealOp(None, Op.mul),
                        TealOp(None, Op.getbit),
                        TealOp(None, Op.store, boolType.stored_value.slot),
                    ]
                )

                actual, _ = expr.__teal__(options)
                actual.addIncoming()
                actual = TealBlock.NormalizeBlocks(actual)

                with TealComponent.Context.ignoreExprEquality():
                    assert actual == expected


def test_Bool_decodeBit():
    boolType = abi.Bool()
    bitIndex = Int(17)
    encoded = Bytes("encoded")
    expr = boolType.decodeBit(encoded, bitIndex)
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.byte, '"encoded"'),
            TealOp(None, Op.int, 17),
            TealOp(None, Op.getbit),
            TealOp(None, Op.store, boolType.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Bool_encode():
    boolType = abi.Bool()
    expr = boolType.encode()
    assert expr.type_of() == TealType.bytes
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.byte, "0x00"),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.load, boolType.stored_value.slot),
            TealOp(None, Op.setbit),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_boolAwareStaticByteLength():
    class ByteLengthTest(NamedTuple):
        types: List[abi.Type]
        expectedLength: int

    tests: List[ByteLengthTest] = [
        ByteLengthTest(types=[], expectedLength=0),
        ByteLengthTest(types=[abi.Uint64()], expectedLength=8),
        ByteLengthTest(types=[abi.Bool()], expectedLength=1),
        ByteLengthTest(types=[abi.Bool()] * 8, expectedLength=1),
        ByteLengthTest(types=[abi.Bool()] * 9, expectedLength=2),
        ByteLengthTest(types=[abi.Bool()] * 16, expectedLength=2),
        ByteLengthTest(types=[abi.Bool()] * 17, expectedLength=3),
        ByteLengthTest(types=[abi.Bool()] * 100, expectedLength=13),
        ByteLengthTest(types=[abi.Bool(), abi.Byte(), abi.Bool()], expectedLength=3),
        ByteLengthTest(
            types=[abi.Bool(), abi.Bool(), abi.Byte(), abi.Bool(), abi.Bool()],
            expectedLength=3,
        ),
        ByteLengthTest(
            types=[abi.Bool()] * 16 + [abi.Byte(), abi.Bool(), abi.Bool()],
            expectedLength=4,
        ),
    ]

    for i, test in enumerate(tests):
        actual = boolAwareStaticByteLength(test.types)
        assert actual == test.expectedLength, "Test at index {} failed".format(i)


def test_consecutiveBoolNum():
    class ConsecutiveTest(NamedTuple):
        types: List[abi.Type]
        start: int
        expected: int

    tests: List[ConsecutiveTest] = [
        ConsecutiveTest(types=[], start=0, expected=0),
        ConsecutiveTest(types=[abi.Uint16()], start=0, expected=0),
        ConsecutiveTest(types=[abi.Bool()], start=0, expected=1),
        ConsecutiveTest(types=[abi.Bool()], start=1, expected=0),
        ConsecutiveTest(types=[abi.Bool(), abi.Bool()], start=0, expected=2),
        ConsecutiveTest(types=[abi.Bool(), abi.Bool()], start=1, expected=1),
        ConsecutiveTest(types=[abi.Bool(), abi.Bool()], start=2, expected=0),
        ConsecutiveTest(types=[abi.Bool() for _ in range(10)], start=0, expected=10),
        ConsecutiveTest(
            types=[abi.Bool(), abi.Bool(), abi.Byte(), abi.Bool()], start=0, expected=2
        ),
        ConsecutiveTest(
            types=[abi.Bool(), abi.Bool(), abi.Byte(), abi.Bool()], start=2, expected=0
        ),
        ConsecutiveTest(
            types=[abi.Bool(), abi.Bool(), abi.Byte(), abi.Bool()], start=3, expected=1
        ),
        ConsecutiveTest(
            types=[abi.Byte(), abi.Bool(), abi.Bool(), abi.Byte()], start=0, expected=0
        ),
        ConsecutiveTest(
            types=[abi.Byte(), abi.Bool(), abi.Bool(), abi.Byte()], start=1, expected=2
        ),
    ]

    for i, test in enumerate(tests):
        actual = consecutiveBoolNum(test.types, test.start)
        assert actual == test.expected, "Test at index {} failed".format(i)


def test_boolSequenceLength():
    class SeqLengthTest(NamedTuple):
        numBools: int
        expectedLength: int

    tests: List[SeqLengthTest] = [
        SeqLengthTest(numBools=0, expectedLength=0),
        SeqLengthTest(numBools=1, expectedLength=1),
        SeqLengthTest(numBools=8, expectedLength=1),
        SeqLengthTest(numBools=9, expectedLength=2),
        SeqLengthTest(numBools=16, expectedLength=2),
        SeqLengthTest(numBools=17, expectedLength=3),
        SeqLengthTest(numBools=100, expectedLength=13),
    ]

    for i, test in enumerate(tests):
        actual = boolSequenceLength(test.numBools)
        assert actual == test.expectedLength, "Test at index {} failed".format(i)


def test_encodeBoolSequence():
    class EncodeSeqTest(NamedTuple):
        types: List[abi.Bool]
        expectedLength: int

    tests: List[EncodeSeqTest] = [
        EncodeSeqTest(types=[], expectedLength=0),
        EncodeSeqTest(types=[abi.Bool()], expectedLength=1),
        EncodeSeqTest(types=[abi.Bool() for _ in range(4)], expectedLength=1),
        EncodeSeqTest(types=[abi.Bool() for _ in range(8)], expectedLength=1),
        EncodeSeqTest(types=[abi.Bool() for _ in range(9)], expectedLength=2),
        EncodeSeqTest(types=[abi.Bool() for _ in range(100)], expectedLength=13),
    ]

    for i, test in enumerate(tests):
        expr = encodeBoolSequence(test.types)
        assert expr.type_of() == TealType.bytes
        assert not expr.has_return()

        setBits = [
            [
                TealOp(None, Op.int, j),
                TealOp(None, Op.load, testType.stored_value.slot),
                TealOp(None, Op.setbit),
            ]
            for j, testType in enumerate(test.types)
        ]

        expected = TealSimpleBlock(
            [
                TealOp(None, Op.byte, "0x" + ("00" * test.expectedLength)),
            ]
            + [expr for setBit in setBits for expr in setBit]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected, "Test at index {} failed".format(i)
