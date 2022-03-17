from typing import List, Tuple, NamedTuple, Callable, Union, Optional
import pytest

from pyteal.ast.abi.uint import UintTypeSpec

from ... import *

options = CompileOptions(version=5)


class UintTestData(NamedTuple):
    uintType: abi.UintTypeSpec
    instanceType: type
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
        uintType=abi.Uint8TypeSpec(),
        instanceType=abi.Uint8,
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
        uintType=abi.Uint16TypeSpec(),
        instanceType=abi.Uint16,
        expectedBits=16,
        maxValue=2 ** 16 - 1,
        checkUpperBound=True,
        expectedDecoding=lambda encoded, startIndex, endIndex, length: ExtractUint16(
            encoded, noneToInt0(startIndex)
        ),
        expectedEncoding=lambda uintType: Suffix(Itob(uintType.get()), Int(6)),
    ),
    UintTestData(
        uintType=abi.Uint32TypeSpec(),
        instanceType=abi.Uint32,
        expectedBits=32,
        maxValue=2 ** 32 - 1,
        checkUpperBound=True,
        expectedDecoding=lambda encoded, startIndex, endIndex, length: ExtractUint32(
            encoded, noneToInt0(startIndex)
        ),
        expectedEncoding=lambda uintType: Suffix(Itob(uintType.get()), Int(4)),
    ),
    UintTestData(
        uintType=abi.Uint64TypeSpec(),
        instanceType=abi.Uint64,
        expectedBits=64,
        maxValue=2 ** 64 - 1,
        checkUpperBound=False,
        expectedDecoding=lambda encoded, startIndex, endIndex, length: Btoi(encoded)
        if startIndex is None and endIndex is None and length is None
        else ExtractUint64(encoded, noneToInt0(startIndex)),
        expectedEncoding=lambda uintType: Itob(uintType.get()),
    ),
]


def test_UintTypeSpec_bits():
    for test in testData:
        assert test.uintType.bit_size() == test.expectedBits
        assert test.uintType.byte_length_static() * 8 == test.expectedBits


def test_UintTypeSpec_str():
    for test in testData:
        assert str(test.uintType) == "uint{}".format(test.expectedBits)
    assert str(abi.ByteTypeSpec()) == "byte"


def test_UintTypeSpec_is_dynamic():
    for test in testData:
        assert not test.uintType.is_dynamic()
    assert not abi.ByteTypeSpec().is_dynamic()


def test_UintTypeSpec_eq():
    for i, test in enumerate(testData):
        assert test.uintType == test.uintType

        for j, otherTest in enumerate(testData):
            if i == j:
                continue
            assert test.uintType != otherTest.uintType

        for otherType in (
            abi.BoolTypeSpec(),
            abi.StaticArrayTypeSpec(test.uintType, 1),
            abi.DynamicArrayTypeSpec(test.uintType),
        ):
            assert test.uintType != otherType

    assert abi.ByteTypeSpec() != abi.Uint8TypeSpec()
    assert abi.Uint8TypeSpec() != abi.ByteTypeSpec()


def test_UintTypeSpec_storage_type():
    for test in testData:
        assert test.uintType.storage_type() == TealType.uint64
    assert abi.BoolTypeSpec().storage_type() == TealType.uint64


def test_UintTypeSpec_new_instance():
    for test in testData:
        assert isinstance(test.uintType.new_instance(), test.instanceType)
    assert isinstance(abi.ByteTypeSpec().new_instance(), abi.Byte)


def test_Uint_set_static():
    for test in testData:
        for value_to_set in (0, 1, 100, test.maxValue):
            value = test.uintType.new_instance()
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
        value = test.uintType.new_instance()
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
        value = test.uintType.new_instance()
        other = test.uintType.new_instance()
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
            value.set(abi.Bool())


def test_Uint_get():
    for test in testData:
        value = test.uintType.new_instance()
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
                    value = test.uintType.new_instance()
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
        value = test.uintType.new_instance()
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
    cases: List[Tuple[UintTypeSpec, UintTypeSpec]] = [
        (abi.Uint8TypeSpec(), abi.ByteTypeSpec()),
        (abi.ByteTypeSpec(), abi.Uint8TypeSpec()),
    ]
    for type_a, type_b in cases:
        type_b_instance = type_b.new_instance()
        other = type_a.new_instance()
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
