import pytest
from typing import cast
import pyteal as pt
from pyteal import abi

from pyteal.ast.abi.address import AddressLength
from pyteal.ast.abi.type_test import ContainerType
from pyteal.ast.abi.util import substring_for_decoding


options = pt.CompileOptions(version=5)


def test_AddressTypeSpec_str():
    assert str(abi.AddressTypeSpec()) == "address"


def test_AddressTypeSpec_is_dynamic():
    assert (abi.AddressTypeSpec()).is_dynamic() is False


def test_AddressTypeSpec_byte_length_static():
    assert (abi.AddressTypeSpec()).byte_length_static() == abi.AddressLength.Bytes


def test_AddressTypeSpec_length_static():
    assert (abi.AddressTypeSpec()).length_static() == abi.AddressLength.Bytes


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


def test_Address_decode():
    address = bytes([0] * abi.AddressLength.Bytes)
    encoded = pt.Bytes(address)

    for start_index in (None, pt.Int(0)):
        for end_index in (None, pt.Int(1)):
            for length in (None, pt.Int(2)):
                value = abi.Address()

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

                expectedExpr = value._stored_value.store(
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


def test_Address_get():
    value = abi.Address()
    expr = value.get()
    assert expr.type_of() == pt.TealType.bytes
    assert expr.has_return() is False

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


def test_Address_set_StaticArray():
    value_to_set = abi.StaticArray(
        abi.StaticArrayTypeSpec(abi.ByteTypeSpec(), abi.AddressLength.Bytes)
    )
    value = abi.Address()
    expr = value.set(value_to_set)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(
                None,
                pt.Op.load,
                cast(pt.ScratchVar, value_to_set._stored_value).slot,
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
        bogus = abi.StaticArray(abi.StaticArrayTypeSpec(abi.ByteTypeSpec(), 10))
        value.set(bogus)


def test_Address_set_str():
    for value_to_set in ("CEZZTYHNTVIZFZWT6X2R474Z2P3Q2DAZAKIRTPBAHL3LZ7W4O6VBROVRQA",):
        value = abi.Address()
        expr = value.set(value_to_set)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.addr, value_to_set),
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
            value.set(" " * 16)


def test_Address_set_bytes():
    for value_to_set in (bytes(32),):
        value = abi.Address()
        expr = value.set(value_to_set)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.byte, f"0x{value_to_set.hex()}"),
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
            value.set(bytes(16))

        with pytest.raises(pt.TealInputError):
            value.set(16)


def test_Address_set_expr():
    for value_to_set in [pt.Global(pt.GlobalField.zero_address)]:
        value = abi.Address()
        expr = value.set(value_to_set)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        vts, _ = value_to_set.__teal__(options)
        expected = pt.TealSimpleBlock(
            [
                vts.ops[0],
                pt.TealOp(
                    None,
                    pt.Op.store,
                    cast(pt.ScratchVar, value._stored_value).slot,
                ),
                pt.TealOp(
                    None,
                    pt.Op.load,
                    cast(pt.ScratchVar, value._stored_value).slot,
                ),
                pt.TealOp(None, pt.Op.len),
                pt.TealOp(None, pt.Op.int, AddressLength.Bytes.value),
                pt.TealOp(None, pt.Op.eq),
                pt.TealOp(None, pt.Op.assert_),
            ]
        )

        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_Address_set_copy():
    value = abi.Address()
    other = abi.Address()
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
        value.set(abi.String())


def test_Address_set_computed():
    av = pt.Addr("MDDKJUCTY57KA2PBFI44CLTJ5YHY5YVS4SVQUPZAWSRV2ZAVFKI33O6YPE")
    computed_value = ContainerType(abi.AddressTypeSpec(), av)

    value = abi.Address()
    expr = value.set(computed_value)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    _, byte_ops = av.__teal__(options)
    expected = pt.TealSimpleBlock(
        [
            byte_ops.ops[0],
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
        value.set(ContainerType(abi.ByteTypeSpec(), pt.Int(0x01)))
