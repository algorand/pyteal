import pyteal as pt
from pyteal import abi

options = pt.CompileOptions(version=5)


def test_Account_str():
    assert str(abi.AccountTypeSpec()) == "account"


def test_AccountTypeSpec_is_dynamic():
    assert not (abi.AccountTypeSpec()).is_dynamic()


def test_AccountTypeSpec_new_instance():
    assert isinstance(abi.AccountTypeSpec().new_instance(), abi.Account)


def test_AccountTypeSpec_eq():
    assert abi.AccountTypeSpec() == abi.AccountTypeSpec()

    for otherType in (
        abi.ByteTypeSpec(),
        abi.Uint8TypeSpec(),
        abi.AddressTypeSpec(),
    ):
        assert abi.AccountTypeSpec() != otherType


def test_Account_typespec():
    assert abi.Account().type_spec() == abi.AccountTypeSpec()


def test_Account_encode():
    value = abi.Account()
    expr = value.encode()
    assert expr.type_of() == pt.TealType.bytes
    assert expr.has_return() is False

    expectEncoding = pt.SetByte(pt.Bytes(b"\x00"), pt.Int(0), value.stored_value.load())

    expected, _ = expectEncoding.__teal__(options)
    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)
    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Account_get():
    value = abi.Account()
    expr = value.get()
    assert expr.type_of() == pt.TealType.uint64
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, pt.Op.load, value.stored_value.slot),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Account_set():
    val_to_set = 2
    value = abi.Account()
    expr = value.set(val_to_set)
    assert expr.type_of() == pt.TealType.none
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, pt.Op.int, val_to_set),
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Account_deref():
    val_to_set = 2
    value = abi.Account()
    value.set(val_to_set)
    expr = value.deref()
    assert expr.type_of() == pt.TealType.bytes
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.load, value.stored_value.slot),
            pt.TealOp(None, pt.Op.txnas, "Accounts"),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Asset_str():
    assert str(abi.AssetTypeSpec()) == "asset"


def test_AssetTypeSpec_is_dynamic():
    assert not (abi.AssetTypeSpec()).is_dynamic()


def test_AssetTypeSpec_new_instance():
    assert isinstance(abi.AssetTypeSpec().new_instance(), abi.Asset)


def test_AssetTypeSpec_eq():
    assert abi.AssetTypeSpec() == abi.AssetTypeSpec()

    for otherType in (
        abi.ByteTypeSpec(),
        abi.Uint8TypeSpec(),
        abi.AddressTypeSpec(),
    ):
        assert abi.AssetTypeSpec() != otherType


def test_Asset_typespec():
    assert abi.Asset().type_spec() == abi.AssetTypeSpec()


def test_Asset_encode():
    value = abi.Asset()
    expr = value.encode()
    assert expr.type_of() == pt.TealType.bytes
    assert expr.has_return() is False

    expectEncoding = pt.SetByte(pt.Bytes(b"\x00"), pt.Int(0), value.stored_value.load())

    expected, _ = expectEncoding.__teal__(options)
    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)
    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Asset_get():
    value = abi.Asset()
    expr = value.get()
    assert expr.type_of() == pt.TealType.uint64
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, pt.Op.load, value.stored_value.slot),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Asset_set():
    val_to_set = 2
    value = abi.Asset()
    expr = value.set(val_to_set)
    assert expr.type_of() == pt.TealType.none
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, pt.Op.int, val_to_set),
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Asset_deref():
    val_to_set = 2
    value = abi.Asset()
    value.set(val_to_set)
    expr = value.deref()
    assert expr.type_of() == pt.TealType.uint64
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.load, value.stored_value.slot),
            pt.TealOp(None, pt.Op.txnas, "Assets"),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Application_str():
    assert str(abi.ApplicationTypeSpec()) == "application"


def test_ApplicationTypeSpec_is_dynamic():
    assert not (abi.ApplicationTypeSpec()).is_dynamic()


def test_ApplicationTypeSpec_new_instance():
    assert isinstance(abi.ApplicationTypeSpec().new_instance(), abi.Application)


def test_ApplicationTypeSpec_eq():
    assert abi.ApplicationTypeSpec() == abi.ApplicationTypeSpec()

    for otherType in (
        abi.ByteTypeSpec(),
        abi.Uint8TypeSpec(),
        abi.AddressTypeSpec(),
    ):
        assert abi.ApplicationTypeSpec() != otherType


def test_Application_typespec():
    assert abi.Application().type_spec() == abi.ApplicationTypeSpec()


def test_Application_encode():
    value = abi.Application()
    expr = value.encode()
    assert expr.type_of() == pt.TealType.bytes
    assert expr.has_return() is False

    expectEncoding = pt.SetByte(pt.Bytes(b"\x00"), pt.Int(0), value.stored_value.load())

    expected, _ = expectEncoding.__teal__(options)
    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)
    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Application_get():
    value = abi.Application()
    expr = value.get()
    assert expr.type_of() == pt.TealType.uint64
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, pt.Op.load, value.stored_value.slot),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Application_set():
    val_to_set = 2
    value = abi.Application()
    expr = value.set(val_to_set)
    assert expr.type_of() == pt.TealType.none
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, pt.Op.int, val_to_set),
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_Application_deref():
    val_to_set = 2
    value = abi.Application()
    value.set(val_to_set)
    expr = value.deref()
    assert expr.type_of() == pt.TealType.uint64
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.load, value.stored_value.slot),
            pt.TealOp(None, pt.Op.txnas, "Applications"),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected
