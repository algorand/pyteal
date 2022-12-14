from typing import NamedTuple, List, cast
import pytest

import pyteal as pt
from pyteal import abi
from pyteal.ast.abi.type_test import ContainerType
from pyteal.ast.abi.bool import (
    _bool_aware_static_byte_length,
    _consecutive_bool_instance_num,
    _consecutive_bool_type_spec_num,
    _bool_sequence_length,
    _encode_bool_sequence,
)

options = pt.CompileOptions(version=5)


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
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.int, 1 if value_to_set else 0),
                pt.TealOp(
                    None,
                    pt.Op.store,
                    cast(pt.ScratchVar, value._stored_value).slot,
                ),
            ]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_Bool_set_expr():
    value = abi.Bool()
    expr = value.set(pt.Int(0).Or(pt.Int(1)))
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.logic_or),
            pt.TealOp(None, pt.Op.logic_not),
            pt.TealOp(None, pt.Op.logic_not),
            pt.TealOp(
                None,
                pt.Op.store,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Bool_set_copy():
    other = abi.Bool()
    value = abi.Bool()
    expr = value.set(other)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(
                None,
                pt.Op.load,
                cast(pt.ScratchVar, other._stored_value).slot,
            ),
            pt.TealOp(
                None,
                pt.Op.store,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        value.set(abi.Uint16())


def test_Bool_set_computed():
    value = abi.Bool()
    computed = ContainerType(abi.BoolTypeSpec(), pt.Int(0x80))
    expr = value.set(computed)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.int, 0x80),
            pt.TealOp(
                None,
                pt.Op.store,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        value.set(ContainerType(abi.Uint32TypeSpec(), pt.Int(65537)))


def test_Bool_get():
    value = abi.Bool()
    expr = value.get()
    assert expr.type_of() == pt.TealType.uint64
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(
                expr,
                pt.Op.load,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
        ]
    )

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_Bool_decode():
    value = abi.Bool()
    encoded = pt.Bytes("encoded")
    for start_index in (None, pt.Int(1)):
        for end_index in (None, pt.Int(2)):
            for length in (None, pt.Int(3)):
                expr = value.decode(
                    encoded, start_index=start_index, end_index=end_index, length=length
                )
                assert expr.type_of() == pt.TealType.none
                assert not expr.has_return()

                expected = pt.TealSimpleBlock(
                    [
                        pt.TealOp(None, pt.Op.byte, '"encoded"'),
                        pt.TealOp(None, pt.Op.int, 0 if start_index is None else 1),
                        pt.TealOp(None, pt.Op.int, 8),
                        pt.TealOp(None, pt.Op.mul),
                        pt.TealOp(None, pt.Op.getbit),
                        pt.TealOp(
                            None,
                            pt.Op.store,
                            cast(pt.ScratchVar, value._stored_value).slot,
                        ),
                    ]
                )

                actual, _ = expr.__teal__(options)
                actual.addIncoming()
                actual = pt.TealBlock.NormalizeBlocks(actual)

                with pt.TealComponent.Context.ignoreExprEquality():
                    assert actual == expected


def test_Bool_decode_bit():
    value = abi.Bool()
    bitIndex = pt.Int(17)
    encoded = pt.Bytes("encoded")
    expr = value.decode_bit(encoded, bitIndex)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, '"encoded"'),
            pt.TealOp(None, pt.Op.int, 17),
            pt.TealOp(None, pt.Op.getbit),
            pt.TealOp(
                None,
                pt.Op.store,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Bool_encode():
    value = abi.Bool()
    expr = value.encode()
    assert expr.type_of() == pt.TealType.bytes
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, "0x00"),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(
                None,
                pt.Op.load,
                cast(pt.ScratchVar, value._stored_value).slot,
            ),
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
        actual = _bool_aware_static_byte_length(test.types)
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
        actual = _consecutive_bool_type_spec_num(test.types, test.start)
        assert actual == test.expected, "Test at index {} failed".format(i)

        actual = _consecutive_bool_instance_num(
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
        actual = _bool_sequence_length(test.numBools)
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
        expr = _encode_bool_sequence(test.types)
        assert expr.type_of() == pt.TealType.bytes
        assert not expr.has_return()

        setBits = [
            [
                pt.TealOp(None, pt.Op.int, j),
                pt.TealOp(
                    None,
                    pt.Op.load,
                    cast(pt.ScratchVar, testType._stored_value).slot,
                ),
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
