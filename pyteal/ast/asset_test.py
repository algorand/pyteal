import pytest

from .. import *

def test_asset_holding_balance():
    expr = AssetHolding.balance(Int(0), Int(17))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.int, 17),
        TealOp(Op.asset_holding_get, "AssetBalance"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_holding_balance_invalid():
    with pytest.raises(TealTypeError):
        AssetHolding.balance(Txn.sender(), Int(17))
    
    with pytest.raises(TealTypeError):
        AssetHolding.balance(Int(0), Txn.receiver())

def test_asset_holding_frozen():
    expr = AssetHolding.frozen(Int(0), Int(17))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.int, 17),
        TealOp(Op.asset_holding_get, "AssetFrozen"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_holding_frozen_invalid():
    with pytest.raises(TealTypeError):
        AssetHolding.frozen(Txn.sender(), Int(17))
    
    with pytest.raises(TealTypeError):
        AssetHolding.frozen(Int(0), Txn.receiver())

def test_asset_param_total():
    expr = AssetParam.total(Int(0))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.asset_params_get, "AssetTotal"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_param_total_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.total(Txn.sender())

def test_asset_param_decimals():
    expr = AssetParam.decimals(Int(0))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.asset_params_get, "AssetDecimals"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_param_decimals_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.decimals(Txn.sender())

def test_asset_param_default_frozen():
    expr = AssetParam.defaultFrozen(Int(0))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.asset_params_get, "AssetDefaultFrozen"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_param_default_frozen_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.defaultFrozen(Txn.sender())

def test_asset_param_unit_name():
    expr = AssetParam.unitName(Int(0))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.asset_params_get, "AssetUnitName"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_param_unit_name_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.unitName(Txn.sender())

def test_asset_param_name():
    expr = AssetParam.name(Int(0))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.asset_params_get, "AssetName"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_param_name_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.name(Txn.sender())

def test_asset_param_url():
    expr = AssetParam.url(Int(0))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.asset_params_get, "AssetURL"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_param_url_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.url(Txn.sender())

def test_asset_param_metadata_hash():
    expr = AssetParam.metadataHash(Int(0))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.asset_params_get, "AssetMetadataHash"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_param_metadata_hash_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.metadataHash(Txn.sender())

def test_asset_param_manager():
    expr = AssetParam.manager(Int(0))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.asset_params_get, "AssetManager"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_param_manager_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.manager(Txn.sender())

def test_asset_param_reserve():
    expr = AssetParam.reserve(Int(2))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.asset_params_get, "AssetReserve"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_param_reserve_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.reserve(Txn.sender())

def test_asset_param_freeze():
    expr = AssetParam.freeze(Int(0))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.asset_params_get, "AssetFreeze"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_param_freeze_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.freeze(Txn.sender())

def test_asset_param_clawback():
    expr = AssetParam.clawback(Int(1))
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.asset_params_get, "AssetClawback"),
        TealOp(Op.store, expr.slotOk),
        TealOp(Op.store, expr.slotValue)
    ]

def test_asset_param_clawback_invalid():
    with pytest.raises(TealTypeError):
        AssetParam.clawback(Txn.sender())
