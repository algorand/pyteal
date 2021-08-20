import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

teal2Options = CompileOptions(version=2)
teal3Options = CompileOptions(version=3)
teal4Options = CompileOptions(version=4)


def test_txn_sender():
    expr = Txn.sender()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "Sender")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_fee():
    expr = Txn.fee()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "Fee")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_first_valid():
    expr = Txn.first_valid()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "FirstValid")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_last_valid():
    expr = Txn.last_valid()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "LastValid")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_note():
    expr = Txn.note()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "Note")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_lease():
    expr = Txn.lease()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "Lease")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_receiver():
    expr = Txn.receiver()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "Receiver")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_amount():
    expr = Txn.amount()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "Amount")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_close_remainder_to():
    expr = Txn.close_remainder_to()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "CloseRemainderTo")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_vote_pk():
    expr = Txn.vote_pk()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "VotePK")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_selection_pk():
    expr = Txn.selection_pk()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "SelectionPK")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_vote_first():
    expr = Txn.vote_first()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "VoteFirst")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_vote_last():
    expr = Txn.vote_last()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "VoteLast")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_vote_key_dilution():
    expr = Txn.vote_key_dilution()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "VoteKeyDilution")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_type():
    expr = Txn.type()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "Type")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_type_enum():
    expr = Txn.type_enum()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "TypeEnum")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_xfer_asset():
    expr = Txn.xfer_asset()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "XferAsset")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_asset_amount():
    expr = Txn.asset_amount()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "AssetAmount")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_asset_sender():
    expr = Txn.asset_sender()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "AssetSender")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_asset_receiver():
    expr = Txn.asset_receiver()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "AssetReceiver")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_asset_close_to():
    expr = Txn.asset_close_to()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "AssetCloseTo")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_group_index():
    expr = Txn.group_index()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "GroupIndex")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_id():
    expr = Txn.tx_id()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "TxID")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_application_id():
    expr = Txn.application_id()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ApplicationID")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_on_completion():
    expr = Txn.on_completion()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "OnCompletion")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_application_args():
    for i in range(32):
        expr = Txn.application_args[i]
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.txna, "ApplicationArgs", i)])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_application_args_length():
    expr = Txn.application_args.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "NumAppArgs")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_accounts():
    for i in range(32):
        expr = Txn.accounts[i]
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.txna, "Accounts", i)])

        actual, _ = expr.__teal__(teal2Options)

        assert actual == expected


def test_txn_accounts_length():
    expr = Txn.accounts.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "NumAccounts")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_approval_program():
    expr = Txn.approval_program()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ApprovalProgram")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_clear_state_program():
    expr = Txn.clear_state_program()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ClearStateProgram")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_rekey_to():
    expr = Txn.rekey_to()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "RekeyTo")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset():
    expr = Txn.config_asset()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAsset")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset_total():
    expr = Txn.config_asset_total()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAssetTotal")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset_decimals():
    expr = Txn.config_asset_decimals()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAssetDecimals")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset_default_frozen():
    expr = Txn.config_asset_default_frozen()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAssetDefaultFrozen")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset_unit_name():
    expr = Txn.config_asset_unit_name()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAssetUnitName")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset_name():
    expr = Txn.config_asset_name()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAssetName")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset_url():
    expr = Txn.config_asset_url()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAssetURL")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset_metadata_hash():
    expr = Txn.config_asset_metadata_hash()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAssetMetadataHash")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset_manager():
    expr = Txn.config_asset_manager()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAssetManager")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset_reserve():
    expr = Txn.config_asset_reserve()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAssetReserve")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset_freeze():
    expr = Txn.config_asset_freeze()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAssetFreeze")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_config_asset_clawback():
    expr = Txn.config_asset_clawback()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ConfigAssetClawback")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_freeze_asset():
    expr = Txn.freeze_asset()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "FreezeAsset")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_freeze_asset_account():
    expr = Txn.freeze_asset_account()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "FreezeAssetAccount")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_freeze_asset_frozen():
    expr = Txn.freeze_asset_frozen()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "FreezeAssetFrozen")])

    actual, _ = expr.__teal__(teal2Options)

    assert actual == expected


def test_txn_assets():
    for i in range(32):
        expr = Txn.assets[i]
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.txna, "Assets", i)])

        actual, _ = expr.__teal__(teal3Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal2Options)


def test_txn_assets_length():
    expr = Txn.assets.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "NumAssets")])

    actual, _ = expr.__teal__(teal3Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_applications():
    for i in range(32):
        expr = Txn.applications[i]
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.txna, "Applications", i)])

        actual, _ = expr.__teal__(teal3Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal2Options)


def test_txn_applications_length():
    expr = Txn.applications.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "NumApplications")])

    actual, _ = expr.__teal__(teal3Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_global_num_uints():
    expr = Txn.global_num_uints()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "GlobalNumUint")])

    actual, _ = expr.__teal__(teal3Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_global_num_byte_slices():
    expr = Txn.global_num_byte_slices()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "GlobalNumByteSlice")])

    actual, _ = expr.__teal__(teal3Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_local_num_uints():
    expr = Txn.local_num_uints()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "LocalNumUint")])

    actual, _ = expr.__teal__(teal3Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_local_num_byte_slices():
    expr = Txn.local_num_byte_slices()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "LocalNumByteSlice")])

    actual, _ = expr.__teal__(teal3Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_txn_extra_program_pages():
    expr = Txn.extra_program_pages()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.txn, "ExtraProgramPages")])

    actual, _ = expr.__teal__(teal4Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)
