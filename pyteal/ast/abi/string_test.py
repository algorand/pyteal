from ... import *

options = CompileOptions(version=5)


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
    assert expr.type_of() == TealType.bytes
    assert expr.has_return() is False

    expected = TealSimpleBlock([TealOp(expr, Op.load, value.stored_value.slot)])
    actual, _ = expr.__teal__(options)
    assert actual == expected


def test_String_decode():
    import random
    from os import urandom

    value = abi.String()
    for value_to_set in [urandom(random.randint(0, 50)) for x in range(10)]:
        expr = value.decode(Bytes(value_to_set))

        assert expr.type_of() == TealType.none
        assert expr.has_return() is False

        expected = TealSimpleBlock(
            [
                TealOp(None, Op.byte, f"0x{value_to_set.hex()}"),
                TealOp(None, Op.store, value.stored_value.slot),
            ]
        )
        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_String_get():
    value = abi.String()
    expr = value.get()
    assert expr.type_of() == TealType.bytes
    assert expr.has_return() is False

    expected = TealSimpleBlock(
        [TealOp(expr, Op.load, value.stored_value.slot), TealOp(None, Op.extract, 2, 0)]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected
