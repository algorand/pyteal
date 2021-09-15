import pytest

from .. import *
from ..types import types_match

# this is not necessary but mypy complains if it's not included
from .. import MAX_GROUP_SIZE, CompileOptions

teal4Options = CompileOptions(version=4)
teal5Options = CompileOptions(version=5)


def test_InnerTxnBuilder_Begin():
    expr = InnerTxnBuilder.Begin()
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock([TealOp(expr, Op.itxn_begin)])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_InnerTxnBuilder_Submit():
    expr = InnerTxnBuilder.Submit()
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock([TealOp(expr, Op.itxn_submit)])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_InnerTxnBuilder_SetField():
    for field in TxnField:
        if field.is_array:
            with pytest.raises(TealInputError):
                InnerTxnBuilder.SetField(field, Int(0))
            continue

        for value, opArgs in (
            (Int(0), (Op.int, 0)),
            (Bytes("value"), (Op.byte, '"value"')),
        ):
            assert field.type_of() in (TealType.uint64, TealType.bytes)

            if not types_match(field.type_of(), value.type_of()):
                with pytest.raises(TealTypeError):
                    InnerTxnBuilder.SetField(field, value)
                continue

            expr = InnerTxnBuilder.SetField(field, value)
            assert expr.type_of() == TealType.none
            assert not expr.has_return()

            expected = TealSimpleBlock(
                [TealOp(value, *opArgs), TealOp(expr, Op.itxn_field, field.arg_name)]
            )

            actual, _ = expr.__teal__(teal5Options)
            actual.addIncoming()
            actual = TealBlock.NormalizeBlocks(actual)

            assert actual == expected

            with pytest.raises(TealInputError):
                expr.__teal__(teal4Options)


def test_InnerTxnBuilder_SetFields():
    cases = (
        ({}, Seq()),
        ({TxnField.amount: Int(5)}, InnerTxnBuilder.SetField(TxnField.amount, Int(5))),
        (
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.close_remainder_to: Txn.sender(),
            },
            Seq(
                InnerTxnBuilder.SetField(TxnField.type_enum, TxnType.Payment),
                InnerTxnBuilder.SetField(TxnField.close_remainder_to, Txn.sender()),
            ),
        ),
    )

    for fields, expectedExpr in cases:
        expr = InnerTxnBuilder.SetFields(fields)
        assert expr.type_of() == TealType.none
        assert not expr.has_return()

        expected, _ = expectedExpr.__teal__(teal5Options)
        expected.addIncoming()
        expected = TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(teal5Options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected

        if len(fields) != 0:
            with pytest.raises(TealInputError):
                expr.__teal__(teal4Options)


def test_txn_sender():
    expr = InnerTxn.sender()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "Sender")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_fee():
    expr = InnerTxn.fee()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "Fee")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_first_valid():
    expr = InnerTxn.first_valid()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "FirstValid")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_last_valid():
    expr = InnerTxn.last_valid()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "LastValid")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_note():
    expr = InnerTxn.note()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "Note")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_lease():
    expr = InnerTxn.lease()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "Lease")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_receiver():
    expr = InnerTxn.receiver()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "Receiver")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_amount():
    expr = InnerTxn.amount()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "Amount")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_close_remainder_to():
    expr = InnerTxn.close_remainder_to()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "CloseRemainderTo")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_vote_pk():
    expr = InnerTxn.vote_pk()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "VotePK")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_selection_pk():
    expr = InnerTxn.selection_pk()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "SelectionPK")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_vote_first():
    expr = InnerTxn.vote_first()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "VoteFirst")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_vote_last():
    expr = InnerTxn.vote_last()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "VoteLast")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_vote_key_dilution():
    expr = InnerTxn.vote_key_dilution()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "VoteKeyDilution")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected


def test_txn_nonparticipation():
    expr = InnerTxn.nonparticipation()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "Nonparticipation")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_type():
    expr = InnerTxn.type()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "Type")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_type_enum():
    expr = InnerTxn.type_enum()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "TypeEnum")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_xfer_asset():
    expr = InnerTxn.xfer_asset()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "XferAsset")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_asset_amount():
    expr = InnerTxn.asset_amount()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "AssetAmount")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_asset_sender():
    expr = InnerTxn.asset_sender()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "AssetSender")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_asset_receiver():
    expr = InnerTxn.asset_receiver()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "AssetReceiver")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_asset_close_to():
    expr = InnerTxn.asset_close_to()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "AssetCloseTo")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_group_index():
    expr = InnerTxn.group_index()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "GroupIndex")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_id():
    expr = InnerTxn.tx_id()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "TxID")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_application_id():
    expr = InnerTxn.application_id()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ApplicationID")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_on_completion():
    expr = InnerTxn.on_completion()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "OnCompletion")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_application_args():
    for i in range(32):
        expr = InnerTxn.application_args[i]
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.itxna, "ApplicationArgs", i)])

        actual, _ = expr.__teal__(teal5Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal4Options)


def test_txn_application_args_length():
    expr = InnerTxn.application_args.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "NumAppArgs")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_accounts():
    for i in range(32):
        expr = InnerTxn.accounts[i]
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.itxna, "Accounts", i)])

        actual, _ = expr.__teal__(teal5Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal4Options)


def test_txn_accounts_length():
    expr = InnerTxn.accounts.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "NumAccounts")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_approval_program():
    expr = InnerTxn.approval_program()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ApprovalProgram")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_clear_state_program():
    expr = InnerTxn.clear_state_program()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ClearStateProgram")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_rekey_to():
    expr = InnerTxn.rekey_to()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "RekeyTo")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset():
    expr = InnerTxn.config_asset()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAsset")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset_total():
    expr = InnerTxn.config_asset_total()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAssetTotal")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset_decimals():
    expr = InnerTxn.config_asset_decimals()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAssetDecimals")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset_default_frozen():
    expr = InnerTxn.config_asset_default_frozen()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAssetDefaultFrozen")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset_unit_name():
    expr = InnerTxn.config_asset_unit_name()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAssetUnitName")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset_name():
    expr = InnerTxn.config_asset_name()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAssetName")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset_url():
    expr = InnerTxn.config_asset_url()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAssetURL")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset_metadata_hash():
    expr = InnerTxn.config_asset_metadata_hash()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAssetMetadataHash")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset_manager():
    expr = InnerTxn.config_asset_manager()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAssetManager")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset_reserve():
    expr = InnerTxn.config_asset_reserve()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAssetReserve")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset_freeze():
    expr = InnerTxn.config_asset_freeze()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAssetFreeze")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_config_asset_clawback():
    expr = InnerTxn.config_asset_clawback()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ConfigAssetClawback")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_created_asset_id():
    expr = InnerTxn.created_asset_id()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "CreatedAssetID")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_freeze_asset():
    expr = InnerTxn.freeze_asset()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "FreezeAsset")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_freeze_asset_account():
    expr = InnerTxn.freeze_asset_account()
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "FreezeAssetAccount")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_freeze_asset_frozen():
    expr = InnerTxn.freeze_asset_frozen()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "FreezeAssetFrozen")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_assets():
    for i in range(32):
        expr = InnerTxn.assets[i]
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.itxna, "Assets", i)])

        actual, _ = expr.__teal__(teal5Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal4Options)


def test_txn_assets_length():
    expr = InnerTxn.assets.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "NumAssets")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_applications():
    for i in range(32):
        expr = InnerTxn.applications[i]
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock([TealOp(expr, Op.itxna, "Applications", i)])

        actual, _ = expr.__teal__(teal5Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal4Options)


def test_txn_applications_length():
    expr = InnerTxn.applications.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "NumApplications")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_global_num_uints():
    expr = InnerTxn.global_num_uints()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "GlobalNumUint")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_global_num_byte_slices():
    expr = InnerTxn.global_num_byte_slices()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "GlobalNumByteSlice")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_local_num_uints():
    expr = InnerTxn.local_num_uints()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "LocalNumUint")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_local_num_byte_slices():
    expr = InnerTxn.local_num_byte_slices()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "LocalNumByteSlice")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_extra_program_pages():
    expr = InnerTxn.extra_program_pages()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "ExtraProgramPages")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_created_application_id():
    expr = InnerTxn.created_application_id()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "CreatedApplicationID")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_txn_logs():
    for i in range(32):
        expr = InnerTxn.logs[i]
        assert expr.type_of() == TealType.bytes

        expected = TealSimpleBlock([TealOp(expr, Op.itxna, "Logs", i)])

        actual, _ = expr.__teal__(teal5Options)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal4Options)


def test_txn_logs_length():
    expr = InnerTxn.logs.length()
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.itxn, "NumLogs")])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)
