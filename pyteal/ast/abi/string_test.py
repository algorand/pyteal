import pytest

import pyteal as pt
from pyteal import abi
from pyteal.ast.abi.util import substring_for_decoding
from pyteal.ast.abi.type_test import ContainerType

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
    for start_index in (None, pt.Int(1)):
        for end_index in (None, pt.Int(2)):
            for length in (None, pt.Int(3)):
                value = stringType.new_instance()

                if end_index is not None and length is not None:
                    with pytest.raises(pt.TealInputError):
                        value.decode(
                            encoded,
                            start_index=start_index,
                            end_index=end_index,
                            length=length,
                        )
                    continue

                expr = value.decode(
                    encoded, start_index=start_index, end_index=end_index, length=length
                )
                assert expr.type_of() == pt.TealType.none
                assert expr.has_return() is False

                expectedExpr = value.stored_value.store(
                    substring_for_decoding(
                        encoded,
                        start_index=start_index,
                        end_index=end_index,
                        length=length,
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


STATIC_SET_TESTCASES: list[tuple[str | bytes | bytearray, bytes]] = [
    ("stringy", b"\x00\x07stringy"),
    ("😀", b"\x00\x04\xf0\x9f\x98\x80"),
    ("0xDEADBEEF", b"\x00\x0a0xDEADBEEF"),
    (bytes(32), b"\x00\x20" + bytes(32)),
    (b"alphabet_soup", b"\x00\x0dalphabet_soup"),
    (bytearray(b"another one"), b"\x00\x0banother one"),
]


@pytest.mark.parametrize("value_to_set, value_encoded", STATIC_SET_TESTCASES)
def test_String_set_static(value_to_set, value_encoded):
    value = abi.String()
    expr = value.set(value_to_set)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.byte, "0x" + value_encoded.hex()),
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_String_set_static_invalid():
    with pytest.raises(pt.TealInputError):
        abi.String().set(42)


def test_String_set_expr():
    for value_to_set in (pt.Bytes("hi"), pt.Bytes("base16", "0xdeadbeef")):
        value = abi.String()
        expr = value.set(value_to_set)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        value_start, value_end = value_to_set.__teal__(options)
        expected_body = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.store, value.stored_value.slot),
                pt.TealOp(None, pt.Op.load, value.stored_value.slot),
                pt.TealOp(None, pt.Op.len),
                pt.TealOp(None, pt.Op.itob),
                pt.TealOp(None, pt.Op.extract, 6, 0),
                pt.TealOp(None, pt.Op.load, value.stored_value.slot),
                pt.TealOp(None, pt.Op.concat),
                pt.TealOp(None, pt.Op.store, value.stored_value.slot),
            ]
        )
        value_end.setNextBlock(expected_body)
        expected = value_start
        expected.addIncoming()
        expected = pt.TealBlock.NormalizeBlocks(expected)

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
