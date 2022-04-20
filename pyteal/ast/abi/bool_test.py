from typing import NamedTuple, List
import pytest

import pyteal as pt
from .type_test import ContainerType
from .bool import (
    boolAwareStaticByteLength,
    consecutiveBoolInstanceNum,
    consecutiveBoolTypeSpecNum,
    boolSequenceLength,
    encodeBoolSequence,
)

options = pt.CompileOptions(version=5)


def test_BoolTypeSpec_str():
    assert str(pt.abi.BoolTypeSpec()) == "bool"


def test_BoolTypeSpec_is_dynamic():
    assert not pt.abi.BoolTypeSpec().is_dynamic()


def test_BoolTypeSpec_byte_length_static():
    assert pt.abi.BoolTypeSpec().byte_length_static() == 1


def test_BoolTypeSpec_new_instance():
    assert isinstance(pt.abi.BoolTypeSpec().new_instance(), pt.abi.Bool)


def test_BoolTypeSpec_eq():
    assert pt.abi.BoolTypeSpec() == pt.abi.BoolTypeSpec()

    for otherType in (
        pt.abi.ByteTypeSpec,
        pt.abi.Uint64TypeSpec,
        pt.abi.StaticArrayTypeSpec(pt.abi.BoolTypeSpec(), 1),
        pt.abi.DynamicArrayTypeSpec(pt.abi.BoolTypeSpec()),
    ):
        assert pt.abi.BoolTypeSpec() != otherType


def test_Bool_set_static():
    value = pt.abi.Bool()
    for value_to_set in (True, False):
        expr = value.set(value_to_set)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.int, 1 if value_to_set else 0),
                pt.TealOp(None, pt.Op.store, value.stored_value.slot),
            ]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_Bool_set_expr():
    value = pt.abi.Bool()
    expr = value.set(pt.Int(0).Or(pt.Int(1)))
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.logic_or),
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
            pt.TealOp(None, pt.Op.load, value.stored_value.slot),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.lt),
            pt.TealOp(None, pt.Op.assert_),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Bool_set_copy():
    other = pt.abi.Bool()
    value = pt.abi.Bool()
    expr = value.set(other)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.load, other.stored_value.slot),
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        value.set(pt.abi.Uint16())


def test_Bool_set_computed():
    value = pt.abi.Bool()
    computed = ContainerType(pt.abi.BoolTypeSpec(), pt.Int(0x80))
    expr = value.set(computed)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.int, 0x80),
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        value.set(ContainerType(pt.abi.Uint32TypeSpec(), pt.Int(65537)))


def test_Bool_get():
    value = pt.abi.Bool()
    expr = value.get()
    assert expr.type_of() == pt.TealType.uint64
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [pt.TealOp(expr, pt.Op.load, value.stored_value.slot)]
    )

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_Bool_decode():
    value = pt.abi.Bool()
    encoded = pt.Bytes("encoded")
    for startIndex in (None, pt.Int(1)):
        for endIndex in (None, pt.Int(2)):
            for length in (None, pt.Int(3)):
                expr = value.decode(
                    encoded, startIndex=startIndex, endIndex=endIndex, length=length
                )
                assert expr.type_of() == pt.TealType.none
                assert not expr.has_return()

                expected = pt.TealSimpleBlock(
                    [
                        pt.TealOp(None, pt.Op.byte, '"encoded"'),
                        pt.TealOp(None, pt.Op.int, 0 if startIndex is None else 1),
                        pt.TealOp(None, pt.Op.int, 8),
                        pt.TealOp(None, pt.Op.mul),
                        pt.TealOp(None, pt.Op.getbit),
                        pt.TealOp(None, pt.Op.store, value.stored_value.slot),
                    ]
                )

                actual, _ = expr.__teal__(options)
                actual.addIncoming()
                actual = pt.TealBlock.NormalizeBlocks(actual)

                with pt.TealComponent.Context.ignoreExprEquality():
                    assert actual == expected


def test_Bool_decodeBit():
    value = pt.abi.Bool()
    bitIndex = pt.Int(17)
    encoded = pt.Bytes("encoded")
    expr = value.decodeBit(encoded, bitIndex)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, '"encoded"'),
            pt.TealOp(None, pt.Op.int, 17),
            pt.TealOp(None, pt.Op.getbit),
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Bool_encode():
    value = pt.abi.Bool()
    expr = value.encode()
    assert expr.type_of() == pt.TealType.bytes
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, "0x00"),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.load, value.stored_value.slot),
            pt.TealOp(None, pt.Op.setbit),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_boolAwareStaticByteLength():
    class ByteLengthTest(NamedTuple):
        types: List[pt.abi.TypeSpec]
        expectedLength: int

    tests: List[ByteLengthTest] = [
        ByteLengthTest(types=[], expectedLength=0),
        ByteLengthTest(types=[pt.abi.Uint64TypeSpec()], expectedLength=8),
        ByteLengthTest(types=[pt.abi.BoolTypeSpec()], expectedLength=1),
        ByteLengthTest(types=[pt.abi.BoolTypeSpec()] * 8, expectedLength=1),
        ByteLengthTest(types=[pt.abi.BoolTypeSpec()] * 9, expectedLength=2),
        ByteLengthTest(types=[pt.abi.BoolTypeSpec()] * 16, expectedLength=2),
        ByteLengthTest(types=[pt.abi.BoolTypeSpec()] * 17, expectedLength=3),
        ByteLengthTest(types=[pt.abi.BoolTypeSpec()] * 100, expectedLength=13),
        ByteLengthTest(
            types=[pt.abi.BoolTypeSpec(), pt.abi.ByteTypeSpec(), pt.abi.BoolTypeSpec()],
            expectedLength=3,
        ),
        ByteLengthTest(
            types=[
                pt.abi.BoolTypeSpec(),
                pt.abi.BoolTypeSpec(),
                pt.abi.ByteTypeSpec(),
                pt.abi.BoolTypeSpec(),
                pt.abi.BoolTypeSpec(),
            ],
            expectedLength=3,
        ),
        ByteLengthTest(
            types=[pt.abi.BoolTypeSpec()] * 16
            + [pt.abi.ByteTypeSpec(), pt.abi.BoolTypeSpec(), pt.abi.BoolTypeSpec()],
            expectedLength=4,
        ),
    ]

    for i, test in enumerate(tests):
        actual = boolAwareStaticByteLength(test.types)
        assert actual == test.expectedLength, "Test at index {} failed".format(i)


def test_consecutiveBool():
    class ConsecutiveTest(NamedTuple):
        types: List[pt.abi.TypeSpec]
        start: int
        expected: int

    tests: List[ConsecutiveTest] = [
        ConsecutiveTest(types=[], start=0, expected=0),
        ConsecutiveTest(types=[pt.abi.Uint16TypeSpec()], start=0, expected=0),
        ConsecutiveTest(types=[pt.abi.BoolTypeSpec()], start=0, expected=1),
        ConsecutiveTest(types=[pt.abi.BoolTypeSpec()], start=1, expected=0),
        ConsecutiveTest(
            types=[pt.abi.BoolTypeSpec(), pt.abi.BoolTypeSpec()], start=0, expected=2
        ),
        ConsecutiveTest(
            types=[pt.abi.BoolTypeSpec(), pt.abi.BoolTypeSpec()], start=1, expected=1
        ),
        ConsecutiveTest(
            types=[pt.abi.BoolTypeSpec(), pt.abi.BoolTypeSpec()], start=2, expected=0
        ),
        ConsecutiveTest(
            types=[pt.abi.BoolTypeSpec() for _ in range(10)], start=0, expected=10
        ),
        ConsecutiveTest(
            types=[
                pt.abi.BoolTypeSpec(),
                pt.abi.BoolTypeSpec(),
                pt.abi.ByteTypeSpec(),
                pt.abi.BoolTypeSpec(),
            ],
            start=0,
            expected=2,
        ),
        ConsecutiveTest(
            types=[
                pt.abi.BoolTypeSpec(),
                pt.abi.BoolTypeSpec(),
                pt.abi.ByteTypeSpec(),
                pt.abi.BoolTypeSpec(),
            ],
            start=2,
            expected=0,
        ),
        ConsecutiveTest(
            types=[
                pt.abi.BoolTypeSpec(),
                pt.abi.BoolTypeSpec(),
                pt.abi.ByteTypeSpec(),
                pt.abi.BoolTypeSpec(),
            ],
            start=3,
            expected=1,
        ),
        ConsecutiveTest(
            types=[
                pt.abi.ByteTypeSpec(),
                pt.abi.BoolTypeSpec(),
                pt.abi.BoolTypeSpec(),
                pt.abi.ByteTypeSpec(),
            ],
            start=0,
            expected=0,
        ),
        ConsecutiveTest(
            types=[
                pt.abi.ByteTypeSpec(),
                pt.abi.BoolTypeSpec(),
                pt.abi.BoolTypeSpec(),
                pt.abi.ByteTypeSpec(),
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
        types: List[pt.abi.Bool]
        expectedLength: int

    tests: List[EncodeSeqTest] = [
        EncodeSeqTest(types=[], expectedLength=0),
        EncodeSeqTest(types=[pt.abi.Bool()], expectedLength=1),
        EncodeSeqTest(types=[pt.abi.Bool() for _ in range(4)], expectedLength=1),
        EncodeSeqTest(types=[pt.abi.Bool() for _ in range(8)], expectedLength=1),
        EncodeSeqTest(types=[pt.abi.Bool() for _ in range(9)], expectedLength=2),
        EncodeSeqTest(types=[pt.abi.Bool() for _ in range(100)], expectedLength=13),
    ]

    for i, test in enumerate(tests):
        expr = encodeBoolSequence(test.types)
        assert expr.type_of() == pt.TealType.bytes
        assert not expr.has_return()

        setBits = [
            [
                pt.TealOp(None, pt.Op.int, j),
                pt.TealOp(None, pt.Op.load, testType.stored_value.slot),
                pt.TealOp(None, pt.Op.setbit),
            ]
            for j, testType in enumerate(test.types)
        ]

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.byte, "0x" + ("00" * test.expectedLength)),
            ]
            + [expr for setBit in setBits for expr in setBit]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected, "Test at index {} failed".format(i)
