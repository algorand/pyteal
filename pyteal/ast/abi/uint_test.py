from typing import NamedTuple, Callable, Union, Optional, Type
import pytest

from ... import *

# this is not necessary but mypy complains if it's not included
from ... import CompileOptions

options = CompileOptions(version=5)


class UintTestData(NamedTuple):
    uintType: Type[abi.Uint]
    expectedBits: int
    maxValue: int
    checkUpperBound: bool
    expectedDecoding: Callable[
        [Expr, Optional[Expr], Optional[Expr], Optional[Expr]], Expr
    ]
    expectedEncoding: Callable[[abi.Uint], Expr]


def noneToInt0(value: Union[None, Expr]):
    if value is None:
        return Int(0)
    return value


testData = [
    UintTestData(
        uintType=abi.Uint8,
        expectedBits=8,
        maxValue=2 ** 8 - 1,
        checkUpperBound=True,
        expectedDecoding=lambda encoded, startIndex, endIndex, length: GetByte(
            encoded, noneToInt0(startIndex)
        ),
        expectedEncoding=lambda uintType: SetByte(
            Bytes(b"\x00"), Int(0), uintType.get()
        ),
    ),
    UintTestData(
        uintType=abi.Uint16,
        expectedBits=16,
        maxValue=2 ** 16 - 1,
        checkUpperBound=True,
        expectedDecoding=lambda encoded, startIndex, endIndex, length: ExtractUint16(
            encoded, noneToInt0(startIndex)
        ),
        expectedEncoding=lambda uintType: Suffix(Itob(uintType.get()), Int(6)),
    ),
    UintTestData(
        uintType=abi.Uint32,
        expectedBits=32,
        maxValue=2 ** 32 - 1,
        checkUpperBound=True,
        expectedDecoding=lambda encoded, startIndex, endIndex, length: ExtractUint32(
            encoded, noneToInt0(startIndex)
        ),
        expectedEncoding=lambda uintType: Suffix(Itob(uintType.get()), Int(4)),
    ),
    UintTestData(
        uintType=abi.Uint64,
        expectedBits=64,
        maxValue=2 ** 64 - 1,
        checkUpperBound=False,
        expectedDecoding=lambda encoded, startIndex, endIndex, length: Btoi(encoded)
        if startIndex is None and endIndex is None and length is None
        else ExtractUint64(encoded, noneToInt0(startIndex)),
        expectedEncoding=lambda uintType: Itob(uintType.get()),
    ),
]


def test_Uint_bits():
    for test in testData:
        assert test.uintType.bit_size() == test.expectedBits
        assert test.uintType.byte_length_static() * 8 == test.expectedBits


def test_Uint_str():
    for test in testData:
        assert str(test.uintType()) == "uint{}".format(test.expectedBits)
    assert str(abi.Byte()) == "byte"


def test_Uint_is_dynamic():
    for test in testData:
        assert not test.uintType.is_dynamic()


def test_Uint_has_same_type_as():
    for i, test in enumerate(testData):
        assert test.uintType.has_same_type_as(test.uintType)
        assert test.uintType.has_same_type_as(test.uintType())

        for j, otherTest in enumerate(testData):
            if i == j:
                continue
            assert not test.uintType.has_same_type_as(otherTest.uintType)
            assert not test.uintType.has_same_type_as(otherTest.uintType())

        for otherType in (
            abi.Bool,
            abi.StaticArray[test.uintType, 1],
            abi.DynamicArray[test.uintType],
        ):
            assert not test.uintType.has_same_type_as(otherType)
            assert not test.uintType.has_same_type_as(otherType())

    assert abi.Byte.has_same_type_as(abi.Uint8)
    assert abi.Byte.has_same_type_as(abi.Uint8())
    assert abi.Uint8.has_same_type_as(abi.Byte)
    assert abi.Uint8.has_same_type_as(abi.Byte())


def test_Uint_storage_type():
    for test in testData:
        assert test.uintType.storage_type() == TealType.uint64


def test_Uint_set_static():
    for test in testData:
        for value_to_set in (0, 1, 100, test.maxValue):
            value = test.uintType()
            expr = value.set(value_to_set)
            assert expr.type_of() == TealType.none
            assert not expr.has_return()

            expected = TealSimpleBlock(
                [
                    TealOp(None, Op.int, value_to_set),
                    TealOp(None, Op.store, value.stored_value.slot),
                ]
            )

            actual, _ = expr.__teal__(options)
            actual.addIncoming()
            actual = TealBlock.NormalizeBlocks(actual)

            with TealComponent.Context.ignoreExprEquality():
                assert actual == expected

        with pytest.raises(TealInputError):
            value.set(test.maxValue + 1)

        with pytest.raises(TealInputError):
            value.set(-1)


def test_Uint_set_expr():
    for test in testData:
        value = test.uintType()
        expr = value.set(Int(10) + Int(1))
        assert expr.type_of() == TealType.none
        assert not expr.has_return()

        upperBoundCheck = []
        if test.checkUpperBound:
            upperBoundCheck = [
                TealOp(None, Op.load, value.stored_value.slot),
                TealOp(None, Op.int, test.maxValue + 1),
                TealOp(None, Op.lt),
                TealOp(None, Op.assert_),
            ]

        expected = TealSimpleBlock(
            [
                TealOp(None, Op.int, 10),
                TealOp(None, Op.int, 1),
                TealOp(None, Op.add),
                TealOp(None, Op.store, value.stored_value.slot),
            ]
            + upperBoundCheck
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_Uint_set_copy():
    for test in testData:
        value = test.uintType()
        other = test.uintType()
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


def test_Uint_get():
    for test in testData:
        value = test.uintType()
        expr = value.get()
        assert expr.type_of() == TealType.uint64
        assert not expr.has_return()

        expected = TealSimpleBlock([TealOp(expr, Op.load, value.stored_value.slot)])

        actual, _ = expr.__teal__(options)

        assert actual == expected


def test_Uint_decode():
    encoded = Bytes("encoded")
    for test in testData:
        for startIndex in (None, Int(1)):
            for endIndex in (None, Int(2)):
                for length in (None, Int(3)):
                    value = test.uintType()
                    expr = value.decode(
                        encoded, startIndex=startIndex, endIndex=endIndex, length=length
                    )
                    assert expr.type_of() == TealType.none
                    assert not expr.has_return()

                    expectedDecoding = value.stored_value.store(
                        test.expectedDecoding(encoded, startIndex, endIndex, length)
                    )
                    expected, _ = expectedDecoding.__teal__(options)
                    expected.addIncoming()
                    expected = TealBlock.NormalizeBlocks(expected)

                    actual, _ = expr.__teal__(options)
                    actual.addIncoming()
                    actual = TealBlock.NormalizeBlocks(actual)

                    with TealComponent.Context.ignoreExprEquality():
                        assert actual == expected


def test_Uint_encode():
    for test in testData:
        value = test.uintType()
        expr = value.encode()
        assert expr.type_of() == TealType.bytes
        assert not expr.has_return()

        expected, _ = test.expectedEncoding(value).__teal__(options)
        expected.addIncoming()
        expected = TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_ByteUint8_mutual_conversion():
    for type_a, type_b in [(abi.Uint8, abi.Byte), (abi.Byte, abi.Uint8)]:
        type_b_instance = type_b()
        other = type_a()
        expr = type_b_instance.set(other)

        assert expr.type_of() == TealType.none
        assert not expr.has_return()

        expected = TealSimpleBlock(
            [
                TealOp(None, Op.load, other.stored_value.slot),
                TealOp(None, Op.store, type_b_instance.stored_value.slot),
            ]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected
