from typing import NamedTuple, List
import pytest

from ... import *
from .type import ContainerType
from .bool import (
    BoolTypeSpec,
    boolAwareStaticByteLength,
    consecutiveBoolInstanceNum,
    consecutiveBoolTypeSpecNum,
    boolSequenceLength,
    encodeBoolSequence,
)

# this is not necessary but mypy complains if it's not included
from ... import CompileOptions

options = CompileOptions(version=5)


def test_BoolTypeSpec_str():
    assert str(abi.BoolTypeSpec()) == "bool"


def test_BoolTypeSpec_is_dynamic():
    assert not abi.BoolTypeSpec().is_dynamic()


def test_BoolTypeSpec_byte_length_static():
    assert abi.BoolTypeSpec().byte_length_static() == 1


def test_BoolTypeSpec_new_instance():
    assert isinstance(abi.BoolTypeSpec().new_instance(), abi.Bool)


def test_BoolTypeSpec_eq():
    assert abi.BoolTypeSpec() == abi.BoolTypeSpec()

    for otherType in (
        abi.ByteTypeSpec,
        abi.Uint64TypeSpec,
        abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 1),
        abi.DynamicArrayTypeSpec(abi.BoolTypeSpec()),
    ):
        assert abi.BoolTypeSpec() != otherType


def test_Bool_set_static():
    value = abi.Bool()
    for value_to_set in (True, False):
        expr = value.set(value_to_set)
        assert expr.type_of() == TealType.none
        assert not expr.has_return()

        expected = TealSimpleBlock(
            [
                TealOp(None, Op.int, 1 if value_to_set else 0),
                TealOp(None, Op.store, value.stored_value.slot),
            ]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_Bool_set_expr():
    value = abi.Bool()
    expr = value.set(Int(0).Or(Int(1)))
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.int, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.logic_or),
            TealOp(None, Op.store, value.stored_value.slot),
            TealOp(None, Op.load, value.stored_value.slot),
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
    value = abi.Bool()
    expr = value.set(other)
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.load, other.stored_value.slot),
            TealOp(None, Op.store, value.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(TealInputError):
        value.set(abi.Uint16())


def test_Bool_set_computed():
    value = abi.Bool()
    computed = ContainerType(BoolTypeSpec(), Int(0x80))
    expr = value.set(computed)
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.int, 0x80),
            TealOp(None, Op.store, value.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(TealInputError):
        value.set(ContainerType(abi.Uint32TypeSpec(), Int(65537)))


def test_Bool_get():
    value = abi.Bool()
    expr = value.get()
    assert expr.type_of() == TealType.uint64
    assert not expr.has_return()

    expected = TealSimpleBlock([TealOp(expr, Op.load, value.stored_value.slot)])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_Bool_decode():
    value = abi.Bool()
    encoded = Bytes("encoded")
    for startIndex in (None, Int(1)):
        for endIndex in (None, Int(2)):
            for length in (None, Int(3)):
                expr = value.decode(
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
                        TealOp(None, Op.store, value.stored_value.slot),
                    ]
                )

                actual, _ = expr.__teal__(options)
                actual.addIncoming()
                actual = TealBlock.NormalizeBlocks(actual)

                with TealComponent.Context.ignoreExprEquality():
                    assert actual == expected


def test_Bool_decodeBit():
    value = abi.Bool()
    bitIndex = Int(17)
    encoded = Bytes("encoded")
    expr = value.decodeBit(encoded, bitIndex)
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.byte, '"encoded"'),
            TealOp(None, Op.int, 17),
            TealOp(None, Op.getbit),
            TealOp(None, Op.store, value.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Bool_encode():
    value = abi.Bool()
    expr = value.encode()
    assert expr.type_of() == TealType.bytes
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.byte, "0x00"),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.load, value.stored_value.slot),
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
        types: List[abi.TypeSpec]
        expectedLength: int

    tests: List[ByteLengthTest] = [
        ByteLengthTest(types=[], expectedLength=0),
        ByteLengthTest(types=[abi.Uint64TypeSpec()], expectedLength=8),
        ByteLengthTest(types=[abi.BoolTypeSpec()], expectedLength=1),
        ByteLengthTest(types=[abi.BoolTypeSpec()] * 8, expectedLength=1),
        ByteLengthTest(types=[abi.BoolTypeSpec()] * 9, expectedLength=2),
        ByteLengthTest(types=[abi.BoolTypeSpec()] * 16, expectedLength=2),
        ByteLengthTest(types=[abi.BoolTypeSpec()] * 17, expectedLength=3),
        ByteLengthTest(types=[abi.BoolTypeSpec()] * 100, expectedLength=13),
        ByteLengthTest(
            types=[abi.BoolTypeSpec(), abi.ByteTypeSpec(), abi.BoolTypeSpec()],
            expectedLength=3,
        ),
        ByteLengthTest(
            types=[
                abi.BoolTypeSpec(),
                abi.BoolTypeSpec(),
                abi.ByteTypeSpec(),
                abi.BoolTypeSpec(),
                abi.BoolTypeSpec(),
            ],
            expectedLength=3,
        ),
        ByteLengthTest(
            types=[abi.BoolTypeSpec()] * 16
            + [abi.ByteTypeSpec(), abi.BoolTypeSpec(), abi.BoolTypeSpec()],
            expectedLength=4,
        ),
    ]

    for i, test in enumerate(tests):
        actual = boolAwareStaticByteLength(test.types)
        assert actual == test.expectedLength, "Test at index {} failed".format(i)


def test_consecutiveBool():
    class ConsecutiveTest(NamedTuple):
        types: List[abi.TypeSpec]
        start: int
        expected: int

    tests: List[ConsecutiveTest] = [
        ConsecutiveTest(types=[], start=0, expected=0),
        ConsecutiveTest(types=[abi.Uint16TypeSpec()], start=0, expected=0),
        ConsecutiveTest(types=[abi.BoolTypeSpec()], start=0, expected=1),
        ConsecutiveTest(types=[abi.BoolTypeSpec()], start=1, expected=0),
        ConsecutiveTest(
            types=[abi.BoolTypeSpec(), abi.BoolTypeSpec()], start=0, expected=2
        ),
        ConsecutiveTest(
            types=[abi.BoolTypeSpec(), abi.BoolTypeSpec()], start=1, expected=1
        ),
        ConsecutiveTest(
            types=[abi.BoolTypeSpec(), abi.BoolTypeSpec()], start=2, expected=0
        ),
        ConsecutiveTest(
            types=[abi.BoolTypeSpec() for _ in range(10)], start=0, expected=10
        ),
        ConsecutiveTest(
            types=[
                abi.BoolTypeSpec(),
                abi.BoolTypeSpec(),
                abi.ByteTypeSpec(),
                abi.BoolTypeSpec(),
            ],
            start=0,
            expected=2,
        ),
        ConsecutiveTest(
            types=[
                abi.BoolTypeSpec(),
                abi.BoolTypeSpec(),
                abi.ByteTypeSpec(),
                abi.BoolTypeSpec(),
            ],
            start=2,
            expected=0,
        ),
        ConsecutiveTest(
            types=[
                abi.BoolTypeSpec(),
                abi.BoolTypeSpec(),
                abi.ByteTypeSpec(),
                abi.BoolTypeSpec(),
            ],
            start=3,
            expected=1,
        ),
        ConsecutiveTest(
            types=[
                abi.ByteTypeSpec(),
                abi.BoolTypeSpec(),
                abi.BoolTypeSpec(),
                abi.ByteTypeSpec(),
            ],
            start=0,
            expected=0,
        ),
        ConsecutiveTest(
            types=[
                abi.ByteTypeSpec(),
                abi.BoolTypeSpec(),
                abi.BoolTypeSpec(),
                abi.ByteTypeSpec(),
            ],
            start=1,
            expected=2,
        ),
    ]

    for i, test in enumerate(tests):
        actual = consecutiveBoolTypeSpecNum(test.types, test.start)
        assert actual == test.expected, "Test at index {} failed".format(i)

        actual = consecutiveBoolInstanceNum(
            [t.new_instance() for t in test.types], test.start
        )
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
