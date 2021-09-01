import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

teal2Options = CompileOptions()
teal4Options = CompileOptions(version=4)
teal5Options = CompileOptions(version=5)


def test_asset_holding_balance():
    args = Int(0), Int(17)
    expr = AssetHolding.balance(args[0], args[1])
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 0),
            TealOp(args[1], Op.int, 17),
            TealOp(expr, Op.asset_holding_get, "AssetBalance"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_holding_balance_direct_ref():
    args = [Txn.sender(), Txn.assets[17]]
    expr = AssetHolding.balance(args[0], args[1])
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.txn, "Sender"),
            TealOp(args[1], Op.txna, "Assets", 17),
            TealOp(expr, Op.asset_holding_get, "AssetBalance"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_holding_balance_invalid():
    with pytest.raises(TealTypeError):
        AssetHolding.balance(Txn.sender(), Bytes("100"))

    with pytest.raises(TealTypeError):
        AssetHolding.balance(Int(0), Txn.receiver())


def test_asset_holding_frozen():
    args = [Int(0), Int(17)]
    expr = AssetHolding.frozen(args[0], args[1])
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 0),
            TealOp(args[1], Op.int, 17),
            TealOp(expr, Op.asset_holding_get, "AssetFrozen"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_holding_frozen_direct_ref():
    args = [Txn.sender(), Txn.assets[17]]
    expr = AssetHolding.frozen(args[0], args[1])
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.txn, "Sender"),
            TealOp(args[1], Op.txna, "Assets", 17),
            TealOp(expr, Op.asset_holding_get, "AssetFrozen"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_holding_frozen_invalid():
    with pytest.raises(TealTypeError):
        AssetHolding.frozen(Txn.sender(), Bytes("17"))

    with pytest.raises(TealTypeError):
        AssetHolding.frozen(Int(0), Txn.receiver())


def test_asset_param_total():
    arg = Int(0)
    expr = AssetParam.total(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 0),
            TealOp(expr, Op.asset_params_get, "AssetTotal"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_total_direct_ref():
    arg = Txn.assets[0]
    expr = AssetParam.total(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.txna, "Assets", 0),
            TealOp(expr, Op.asset_params_get, "AssetTotal"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_total_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.total(Txn.sender())


def test_asset_param_decimals():
    arg = Int(0)
    expr = AssetParam.decimals(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 0),
            TealOp(expr, Op.asset_params_get, "AssetDecimals"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_decimals_direct_ref():
    arg = Txn.assets[0]
    expr = AssetParam.decimals(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.txna, "Assets", 0),
            TealOp(expr, Op.asset_params_get, "AssetDecimals"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_decimals_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.decimals(Txn.sender())


def test_asset_param_default_frozen():
    arg = Int(0)
    expr = AssetParam.defaultFrozen(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 0),
            TealOp(expr, Op.asset_params_get, "AssetDefaultFrozen"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_default_frozen_direct_ref():
    arg = Txn.assets[0]
    expr = AssetParam.defaultFrozen(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.txna, "Assets", 0),
            TealOp(expr, Op.asset_params_get, "AssetDefaultFrozen"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_default_frozen_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.defaultFrozen(Txn.sender())


def test_asset_param_unit_name():
    arg = Int(0)
    expr = AssetParam.unitName(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 0),
            TealOp(expr, Op.asset_params_get, "AssetUnitName"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_unit_name_direct_ref():
    arg = Txn.assets[0]
    expr = AssetParam.unitName(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.txna, "Assets", 0),
            TealOp(expr, Op.asset_params_get, "AssetUnitName"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_unit_name_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.unitName(Txn.sender())


def test_asset_param_name():
    arg = Int(0)
    expr = AssetParam.name(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 0),
            TealOp(expr, Op.asset_params_get, "AssetName"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_name_direct_ref():
    arg = Txn.assets[0]
    expr = AssetParam.name(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.txna, "Assets", 0),
            TealOp(expr, Op.asset_params_get, "AssetName"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_name_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.name(Txn.sender())


def test_asset_param_url():
    arg = Int(0)
    expr = AssetParam.url(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 0),
            TealOp(expr, Op.asset_params_get, "AssetURL"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_url_direct_ref():
    arg = Txn.assets[0]
    expr = AssetParam.url(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.txna, "Assets", 0),
            TealOp(expr, Op.asset_params_get, "AssetURL"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_url_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.url(Txn.sender())


def test_asset_param_metadata_hash():
    arg = Int(0)
    expr = AssetParam.metadataHash(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 0),
            TealOp(expr, Op.asset_params_get, "AssetMetadataHash"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_metadata_hash_direct_ref():
    arg = Txn.assets[0]
    expr = AssetParam.metadataHash(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.txna, "Assets", 0),
            TealOp(expr, Op.asset_params_get, "AssetMetadataHash"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_metadata_hash_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.metadataHash(Txn.sender())


def test_asset_param_manager():
    arg = Int(0)
    expr = AssetParam.manager(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 0),
            TealOp(expr, Op.asset_params_get, "AssetManager"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_manager_direct_ref():
    arg = Txn.assets[0]
    expr = AssetParam.manager(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.txna, "Assets", 0),
            TealOp(expr, Op.asset_params_get, "AssetManager"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_manager_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.manager(Txn.sender())


def test_asset_param_reserve():
    arg = Int(2)
    expr = AssetParam.reserve(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 2),
            TealOp(expr, Op.asset_params_get, "AssetReserve"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_reserve_direct_ref():
    arg = Txn.assets[2]
    expr = AssetParam.reserve(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.txna, "Assets", 2),
            TealOp(expr, Op.asset_params_get, "AssetReserve"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_reserve_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.reserve(Txn.sender())


def test_asset_param_freeze():
    arg = Int(0)
    expr = AssetParam.freeze(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 0),
            TealOp(expr, Op.asset_params_get, "AssetFreeze"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_freeze_direct_ref():
    arg = Txn.assets[0]
    expr = AssetParam.freeze(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.txna, "Assets", 0),
            TealOp(expr, Op.asset_params_get, "AssetFreeze"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_freeze_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.freeze(Txn.sender())


def test_asset_param_clawback():
    arg = Int(1)
    expr = AssetParam.clawback(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.asset_params_get, "AssetClawback"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_clawback_direct_ref():
    arg = Txn.assets[1]
    expr = AssetParam.clawback(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.txna, "Assets", 1),
            TealOp(expr, Op.asset_params_get, "AssetClawback"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_clawback_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.clawback(Txn.sender())


def test_asset_param_creator_valid():
    arg = Int(1)
    expr = AssetParam.creator(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.asset_params_get, "AssetCreator"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_asset_param_creator_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.creator(Txn.sender())
