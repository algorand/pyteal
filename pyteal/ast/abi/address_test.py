import pyteal as pt
from pyteal import abi

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
        abi.ByteTypeSpec,
        abi.StaticArrayTypeSpec(abi.ByteTypeSpec(), 31),
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
    from os import urandom

    value = abi.Address()
    for value_to_set in [urandom(abi.ADDRESS_LENGTH) for x in range(10)]:
        expr = value.decode(pt.Bytes(value_to_set))

        assert expr.type_of() == pt.TealType.none
        assert expr.has_return() is False

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.byte, f"0x{value_to_set.hex()}"),
                pt.TealOp(None, pt.Op.store, value.stored_value.slot),
            ]
        )
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
