import pytest

import pyteal as pt
from pyteal import abi
from .util import substringForDecoding

options = pt.CompileOptions(version=5)


def test_AddressTypeSpec_str():
    assert str(abi.AddressTypeSpec()) == "address"


def test_AddressTypeSpec_is_dynamic():
    assert (abi.AddressTypeSpec()).is_dynamic() is False


def test_AddressTypeSpec_byte_length_static():
    assert (abi.AddressTypeSpec()).byte_length_static() == abi.ADDRESS_LENGTH


def test_AddressTypeSpec_new_instance():
    assert isinstance(abi.AddressTypeSpec().new_instance(), abi.Address)


def test_AddressTypeSpec_eq():
    assert abi.AddressTypeSpec() == abi.AddressTypeSpec()

    for otherType in (
        abi.ByteTypeSpec(),
        abi.StaticArrayTypeSpec(abi.ByteTypeSpec(), 32),
        abi.DynamicArrayTypeSpec(abi.ByteTypeSpec()),
    ):
        assert abi.AddressTypeSpec() != otherType


def test_Address_encode():
    value = abi.Address()
    expr = value.encode()
    assert expr.type_of() == pt.TealType.bytes
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [pt.TealOp(expr, pt.Op.load, value.stored_value.slot)]
    )
    actual, _ = expr.__teal__(options)
    assert actual == expected


def test_Address_decode():
    address = bytes([0] * abi.ADDRESS_LENGTH)
    encoded = pt.Bytes(address)

    for startIndex in (None, pt.Int(0)):
        for endIndex in (None, pt.Int(1)):
            for length in (None, pt.Int(2)):
                value = abi.Address()

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


def test_Address_get():
    value = abi.Address()
    expr = value.get()
    assert expr.type_of() == pt.TealType.bytes
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [pt.TealOp(expr, pt.Op.load, value.stored_value.slot)]
    )
    actual, _ = expr.__teal__(options)
    assert actual == expected
