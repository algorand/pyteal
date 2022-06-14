import pytest

import pyteal as pt
from pyteal import abi
from pyteal.ast.abi.util import substringForDecoding
from pyteal.ast.abi.type_test import ContainerType
from pyteal.util import escapeStr

options = pt.CompileOptions(version=5)


def test_StringTypeSpec_str():
    assert str(abi.StringTypeSpec()) == "string"


def test_StringTypeSpec_is_dynamic():
    assert (abi.StringTypeSpec()).is_dynamic()


def test_StringTypeSpec_new_instance():
    assert isinstance(abi.StringTypeSpec().new_instance(), abi.String)


def test_StringTypeSpec_eq():
    assert abi.StringTypeSpec() == abi.StringTypeSpec()

    for otherType in (
        abi.ByteTypeSpec(),
        abi.StaticArrayTypeSpec(abi.ByteTypeSpec(), 1),
        abi.DynamicArrayTypeSpec(abi.Uint8TypeSpec()),
        abi.DynamicArrayTypeSpec(abi.ByteTypeSpec()),
    ):
        assert abi.StringTypeSpec() != otherType


def test_String_encode():
    value = abi.String()
    expr = value.encode()
    assert expr.type_of() == pt.TealType.bytes
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [pt.TealOp(expr, pt.Op.load, value.stored_value.slot)]
    )
    actual, _ = expr.__teal__(options)
    assert actual == expected


def test_DynamicArray_decode():
    encoded = pt.Bytes("encoded")
    stringType = abi.StringTypeSpec()
    for startIndex in (None, pt.Int(1)):
        for endIndex in (None, pt.Int(2)):
            for length in (None, pt.Int(3)):
                value = stringType.new_instance()

                if endIndex is not None and length is not None:
                    with pytest.raises(pt.TealInputError):
                        value.decode(
                            encoded,
                            start_index=startIndex,
                            end_index=endIndex,
                            length=length,
                        )
                    continue

                expr = value.decode(
                    encoded, start_index=startIndex, end_index=endIndex, length=length
                )
                assert expr.type_of() == pt.TealType.none
                assert expr.has_return() is False

                expectedExpr = value.stored_value.store(
                    substringForDecoding(
                        encoded, startIndex=startIndex, endIndex=endIndex, length=length
                    )
                )
                expected, _ = expectedExpr.__teal__(options)
                expected.addIncoming()
                expected = pt.TealBlock.NormalizeBlocks(expected)

                actual, _ = expr.__teal__(options)
                actual.addIncoming()
                actual = pt.TealBlock.NormalizeBlocks(actual)

                with pt.TealComponent.Context.ignoreExprEquality():
                    assert actual == expected


def test_String_get():
    value = abi.String()
    expr = value.get()
    assert expr.type_of() == pt.TealType.bytes
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, pt.Op.load, value.stored_value.slot),
            pt.TealOp(None, pt.Op.extract, 2, 0),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_String_set_static():

    for value_to_set in ("stringy", "😀", "0xDEADBEEF"):
        value = abi.String()
        expr = value.set(value_to_set)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.byte, escapeStr(value_to_set)),
                pt.TealOp(None, pt.Op.len),
                pt.TealOp(None, pt.Op.itob),
                pt.TealOp(None, pt.Op.extract, 6, 0),
                pt.TealOp(None, pt.Op.byte, escapeStr(value_to_set)),
                pt.TealOp(None, pt.Op.concat),
                pt.TealOp(None, pt.Op.store, value.stored_value.slot),
            ]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected

    for value_to_set in (bytes(32), b"alphabet_soup"):
        value = abi.String()
        expr = value.set(value_to_set)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        teal_val = f"0x{value_to_set.hex()}"

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.byte, teal_val),
                pt.TealOp(None, pt.Op.len),
                pt.TealOp(None, pt.Op.itob),
                pt.TealOp(None, pt.Op.extract, 6, 0),
                pt.TealOp(None, pt.Op.byte, teal_val),
                pt.TealOp(None, pt.Op.concat),
                pt.TealOp(None, pt.Op.store, value.stored_value.slot),
            ]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected

    with pytest.raises(pt.TealInputError):
        value.set(42)


def test_String_set_expr():
    for value_to_set in (pt.Bytes("hi"), pt.Bytes("base16", "0xdeadbeef")):
        value = abi.String()
        expr = value.set(value_to_set)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        vts, _ = value_to_set.__teal__(options)
        expected = pt.TealSimpleBlock(
            [
                vts.ops[0],
                pt.TealOp(None, pt.Op.len),
                pt.TealOp(None, pt.Op.itob),
                pt.TealOp(None, pt.Op.extract, 6, 0),
                vts.ops[0],
                pt.TealOp(None, pt.Op.concat),
                pt.TealOp(None, pt.Op.store, value.stored_value.slot),
            ]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_String_set_copy():
    value = abi.String()
    other = abi.String()
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
        value.set(abi.Address())


def test_String_set_computed():
    bv = pt.Bytes("base16", "0x0004DEADBEEF")
    computed_value = ContainerType(abi.StringTypeSpec(), bv)

    value = abi.String()
    expr = value.set(computed_value)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    _, byte_ops = bv.__teal__(options)
    expected = pt.TealSimpleBlock(
        [
            byte_ops.ops[0],
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        value.set(ContainerType(abi.ByteTypeSpec(), pt.Int(0x01)))
