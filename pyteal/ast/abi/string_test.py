import pytest

import pyteal as pt
from pyteal import abi
from .util import substringForDecoding


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
                            startIndex=startIndex,
                            endIndex=endIndex,
                            length=length,
                        )
                    continue

                expr = value.decode(
                    encoded, startIndex=startIndex, endIndex=endIndex, length=length
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
