import pytest

import pyteal as pt
from pyteal import abi

options = pt.CompileOptions(version=5)


def test_ReferenceTypeSpecs_list():
    assert abi.ReferenceTypeSpecs == [
        abi.AccountTypeSpec(),
        abi.AssetTypeSpec(),
        abi.ApplicationTypeSpec(),
    ]


def test_ReferenceType_referenced_index():
    for value in (abi.Account(), abi.Asset(), abi.Application()):
        expr = value.referenced_index()
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


def test_ReferenceType_encode():
    for value in (abi.Account(), abi.Asset(), abi.Application()):
        with pytest.raises(
            pt.TealInputError, match=r"A ReferenceType cannot be encoded$"
        ):
            value.encode()


def test_ReferenceType_decode():
    encoded = pt.Bytes("encoded")
    for value in (abi.Account(), abi.Asset(), abi.Application()):
        for start_index in (None, pt.Int(1)):
            for end_index in (None, pt.Int(2)):
                for length in (None, pt.Int(3)):
                    expr = value.decode(
                        encoded,
                        start_index=start_index,
                        end_index=end_index,
                        length=length,
                    )
                    assert expr.type_of() == pt.TealType.none
                    assert expr.has_return() is False

                    expected_decoding = value.stored_value.store(
                        pt.GetByte(
                            encoded,
                            start_index if start_index is not None else pt.Int(0),
                        )
                    )
                    expected, _ = expected_decoding.__teal__(options)
                    expected.addIncoming()
                    expected = pt.TealBlock.NormalizeBlocks(expected)

                    actual, _ = expr.__teal__(options)
                    actual.addIncoming()
                    actual = pt.TealBlock.NormalizeBlocks(actual)

                    with pt.TealComponent.Context.ignoreExprEquality():
                        assert actual == expected


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


def test_Account_address():
    value = abi.Account()
    expr = value.address()
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


def test_Account_params():
    value = abi.Account()

    params = value.params()

    assert type(params) is pt.AccountParamObject

    expected = value.referenced_index()
    actual = params._account

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual.__teal__(options) == expected.__teal__(options)


def test_Account_asset_holding():
    value = abi.Account()

    assets = ((pt.Int(6), pt.Int(6)), (a := abi.Asset(), a.referenced_index()))

    for asset, expected_asset in assets:
        holding = value.asset_holding(asset)

        assert type(holding) is pt.AssetHoldingObject

        expected_account = value.referenced_index()
        actual_account = holding._account

        actual_asset = holding._asset

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual_account.__teal__(options) == expected_account.__teal__(
                options
            )
            assert actual_asset.__teal__(options) == expected_asset.__teal__(options)


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


def test_Asset_asset_id():
    value = abi.Asset()
    expr = value.asset_id()
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


def test_Asset_holding():
    value = abi.Asset()

    accounts = (
        (pt.Int(6), pt.Int(6)),
        (
            pt.Addr("QSA6K5MNJPEGO5SDSWXBM3K4UEI3Q2NCPS2OUXVJI5QPCHMVI27MFRSHKI"),
            pt.Addr("QSA6K5MNJPEGO5SDSWXBM3K4UEI3Q2NCPS2OUXVJI5QPCHMVI27MFRSHKI"),
        ),
        (a := abi.Account(), a.referenced_index()),
    )

    for account, expected_account in accounts:
        holding = value.holding(account)

        assert type(holding) is pt.AssetHoldingObject

        expected_asset = value.referenced_index()
        actual_asset = holding._asset

        actual_account = holding._account

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual_asset.__teal__(options) == expected_asset.__teal__(options)
            assert actual_account.__teal__(options) == expected_account.__teal__(
                options
            )


def test_Asset_params():
    value = abi.Asset()

    params = value.params()

    assert type(params) is pt.AssetParamObject

    expected = value.referenced_index()
    actual = params._asset

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual.__teal__(options) == expected.__teal__(options)


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


def test_Application_application_id():
    value = abi.Application()
    expr = value.application_id()
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


def test_Application_params():
    value = abi.Application()

    params = value.params()

    assert type(params) is pt.AppParamObject

    expected = value.referenced_index()
    actual = params._app

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual.__teal__(options) == expected.__teal__(options)
