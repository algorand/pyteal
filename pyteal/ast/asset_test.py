import pytest

import pyteal as pt
from pyteal.ast.maybe_test import assert_MaybeValue_equality

avm2Options = pt.CompileOptions()
avm4Options = pt.CompileOptions(version=4)
avm5Options = pt.CompileOptions(version=5)


def test_asset_holding_balance():
    args = pt.Int(0), pt.Int(17)
    expr = pt.AssetHolding.balance(args[0], args[1])
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 0),
            pt.TealOp(args[1], pt.Op.int, 17),
            pt.TealOp(expr, pt.Op.asset_holding_get, "AssetBalance"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_holding_balance_direct_ref():
    args = [pt.Txn.sender(), pt.Txn.assets[17]]
    expr = pt.AssetHolding.balance(args[0], args[1])
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.txn, "Sender"),
            pt.TealOp(args[1], pt.Op.txna, "Assets", 17),
            pt.TealOp(expr, pt.Op.asset_holding_get, "AssetBalance"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_holding_balance_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetHolding.balance(pt.Txn.sender(), pt.Bytes("100"))

    with pytest.raises(pt.TealTypeError):
        pt.AssetHolding.balance(pt.Int(0), pt.Txn.receiver())


def test_asset_holding_frozen():
    args = [pt.Int(0), pt.Int(17)]
    expr = pt.AssetHolding.frozen(args[0], args[1])
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 0),
            pt.TealOp(args[1], pt.Op.int, 17),
            pt.TealOp(expr, pt.Op.asset_holding_get, "AssetFrozen"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_holding_frozen_direct_ref():
    args = [pt.Txn.sender(), pt.Txn.assets[17]]
    expr = pt.AssetHolding.frozen(args[0], args[1])
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.txn, "Sender"),
            pt.TealOp(args[1], pt.Op.txna, "Assets", 17),
            pt.TealOp(expr, pt.Op.asset_holding_get, "AssetFrozen"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_holding_frozen_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetHolding.frozen(pt.Txn.sender(), pt.Bytes("17"))

    with pytest.raises(pt.TealTypeError):
        pt.AssetHolding.frozen(pt.Int(0), pt.Txn.receiver())


def test_asset_param_total():
    arg = pt.Int(0)
    expr = pt.AssetParam.total(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetTotal"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_total_direct_ref():
    arg = pt.Txn.assets[0]
    expr = pt.AssetParam.total(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.txna, "Assets", 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetTotal"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_total_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.total(pt.Txn.sender())


def test_asset_param_decimals():
    arg = pt.Int(0)
    expr = pt.AssetParam.decimals(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetDecimals"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_decimals_direct_ref():
    arg = pt.Txn.assets[0]
    expr = pt.AssetParam.decimals(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.txna, "Assets", 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetDecimals"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_decimals_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.decimals(pt.Txn.sender())


def test_asset_param_default_frozen():
    arg = pt.Int(0)
    expr = pt.AssetParam.defaultFrozen(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetDefaultFrozen"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_default_frozen_direct_ref():
    arg = pt.Txn.assets[0]
    expr = pt.AssetParam.defaultFrozen(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.txna, "Assets", 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetDefaultFrozen"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_default_frozen_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.defaultFrozen(pt.Txn.sender())


def test_asset_param_unit_name():
    arg = pt.Int(0)
    expr = pt.AssetParam.unitName(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetUnitName"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_unit_name_direct_ref():
    arg = pt.Txn.assets[0]
    expr = pt.AssetParam.unitName(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.txna, "Assets", 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetUnitName"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_unit_name_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.unitName(pt.Txn.sender())


def test_asset_param_name():
    arg = pt.Int(0)
    expr = pt.AssetParam.name(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetName"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_name_direct_ref():
    arg = pt.Txn.assets[0]
    expr = pt.AssetParam.name(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.txna, "Assets", 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetName"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_name_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.name(pt.Txn.sender())


def test_asset_param_url():
    arg = pt.Int(0)
    expr = pt.AssetParam.url(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetURL"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_url_direct_ref():
    arg = pt.Txn.assets[0]
    expr = pt.AssetParam.url(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.txna, "Assets", 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetURL"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_url_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.url(pt.Txn.sender())


def test_asset_param_metadata_hash():
    arg = pt.Int(0)
    expr = pt.AssetParam.metadataHash(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetMetadataHash"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_metadata_hash_direct_ref():
    arg = pt.Txn.assets[0]
    expr = pt.AssetParam.metadataHash(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.txna, "Assets", 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetMetadataHash"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_metadata_hash_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.metadataHash(pt.Txn.sender())


def test_asset_param_manager():
    arg = pt.Int(0)
    expr = pt.AssetParam.manager(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetManager"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_manager_direct_ref():
    arg = pt.Txn.assets[0]
    expr = pt.AssetParam.manager(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.txna, "Assets", 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetManager"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_manager_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.manager(pt.Txn.sender())


def test_asset_param_reserve():
    arg = pt.Int(2)
    expr = pt.AssetParam.reserve(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 2),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetReserve"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_reserve_direct_ref():
    arg = pt.Txn.assets[2]
    expr = pt.AssetParam.reserve(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.txna, "Assets", 2),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetReserve"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_reserve_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.reserve(pt.Txn.sender())


def test_asset_param_freeze():
    arg = pt.Int(0)
    expr = pt.AssetParam.freeze(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetFreeze"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_freeze_direct_ref():
    arg = pt.Txn.assets[0]
    expr = pt.AssetParam.freeze(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.txna, "Assets", 0),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetFreeze"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_freeze_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.freeze(pt.Txn.sender())


def test_asset_param_clawback():
    arg = pt.Int(1)
    expr = pt.AssetParam.clawback(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetClawback"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_clawback_direct_ref():
    arg = pt.Txn.assets[1]
    expr = pt.AssetParam.clawback(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.txna, "Assets", 1),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetClawback"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_clawback_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.clawback(pt.Txn.sender())


def test_asset_param_creator_valid():
    arg = pt.Int(1)
    expr = pt.AssetParam.creator(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.asset_params_get, "AssetCreator"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_creator_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AssetParam.creator(pt.Txn.sender())


def test_AssetHoldingObject():
    for asset in (pt.Int(1), pt.Int(100)):
        for account in (
            pt.Int(7),
            pt.Addr("QSA6K5MNJPEGO5SDSWXBM3K4UEI3Q2NCPS2OUXVJI5QPCHMVI27MFRSHKI"),
        ):
            obj = pt.AssetHoldingObject(asset, account)

            assert obj._asset is asset
            assert obj._account is account

            assert_MaybeValue_equality(
                obj.balance(), pt.AssetHolding.balance(account, asset), avm5Options
            )
            assert_MaybeValue_equality(
                obj.frozen(), pt.AssetHolding.frozen(account, asset), avm5Options
            )


def test_AssetParamObject():
    for asset in (pt.Int(1), pt.Int(100)):
        obj = pt.AssetParamObject(asset)

        assert obj._asset is asset

        assert_MaybeValue_equality(obj.total(), pt.AssetParam.total(asset), avm5Options)
        assert_MaybeValue_equality(
            obj.decimals(), pt.AssetParam.decimals(asset), avm5Options
        )
        assert_MaybeValue_equality(
            obj.default_frozen(), pt.AssetParam.defaultFrozen(asset), avm5Options
        )
        assert_MaybeValue_equality(
            obj.unit_name(), pt.AssetParam.unitName(asset), avm5Options
        )
        assert_MaybeValue_equality(obj.name(), pt.AssetParam.name(asset), avm5Options)
        assert_MaybeValue_equality(obj.url(), pt.AssetParam.url(asset), avm5Options)
        assert_MaybeValue_equality(
            obj.metadata_hash(), pt.AssetParam.metadataHash(asset), avm5Options
        )
        assert_MaybeValue_equality(
            obj.manager_address(), pt.AssetParam.manager(asset), avm5Options
        )
        assert_MaybeValue_equality(
            obj.reserve_address(), pt.AssetParam.reserve(asset), avm5Options
        )
        assert_MaybeValue_equality(
            obj.freeze_address(), pt.AssetParam.freeze(asset), avm5Options
        )
        assert_MaybeValue_equality(
            obj.clawback_address(), pt.AssetParam.clawback(asset), avm5Options
        )
        assert_MaybeValue_equality(
            obj.creator_address(), pt.AssetParam.creator(asset), avm5Options
        )
