import pyteal as pt
from pyteal import abi

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
        abi.ByteTypeSpec,
        abi.StaticArrayTypeSpec(abi.ByteTypeSpec(), 1),
        abi.DynamicArrayTypeSpec(abi.Uint8TypeSpec()),
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


def test_String_decode():
    import random
    from os import urandom

    value = abi.String()
    for value_to_set in [urandom(random.randint(0, 50)) for x in range(10)]:
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
