import pytest

from .. import *

GTXN_RANGE = range(MAX_GROUP_SIZE)

def test_gtxn_invalid():
    with pytest.raises(TealInputError):
        Gtxn(-1, TxnField.fee)

    with pytest.raises(TealInputError):
        Gtxn(MAX_GROUP_SIZE+1, TxnField.sender)

def test_gtxn_sender():
    for i in GTXN_RANGE:
        expr = Gtxn.sender(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Sender")
        ]

def test_gtxn_fee():
    for i in GTXN_RANGE:
        expr = Gtxn.fee(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Fee")
        ]

def test_gtxn_first_valid():
    for i in GTXN_RANGE:
        expr = Gtxn.first_valid(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "FirstValid")
        ]

def test_gtxn_last_valid():
    for i in GTXN_RANGE:
        expr = Gtxn.last_valid(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "LastValid")
        ]

def test_gtxn_note():
    for i in GTXN_RANGE:
        expr = Gtxn.note(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Note")
        ]

def test_gtxn_lease():
    for i in GTXN_RANGE:
        expr = Gtxn.lease(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Lease")
        ]

def test_gtxn_receiver():
    for i in GTXN_RANGE:
        expr = Gtxn.receiver(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Receiver")
        ]

def test_gtxn_amount():
    for i in GTXN_RANGE:
        expr = Gtxn.amount(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Amount")
        ]

def test_gtxn_close_remainder_to():
    for i in GTXN_RANGE:
        expr = Gtxn.close_remainder_to(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "CloseRemainderTo")
        ]

def test_gtxn_vote_pk():
    for i in GTXN_RANGE:
        expr = Gtxn.vote_pk(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "VotePK")
        ]

def test_gtxn_selection_pk():
    for i in GTXN_RANGE:
        expr = Gtxn.selection_pk(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "SelectionPK")
        ]

def test_gtxn_vote_first():
    for i in GTXN_RANGE:
        expr = Gtxn.vote_first(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "VoteFirst")
        ]

def test_gtxn_vote_last():
    for i in GTXN_RANGE:
        expr = Gtxn.vote_last(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "VoteLast")
        ]

def test_gtxn_vote_key_dilution():
    for i in GTXN_RANGE:
        expr = Gtxn.vote_key_dilution(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "VoteKeyDilution")
        ]

def test_gtxn_type():
    for i in GTXN_RANGE:
        expr = Gtxn.type(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Type")
        ]

def test_gtxn_type_enum():
    for i in GTXN_RANGE:
        expr = Gtxn.type_enum(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "TypeEnum")
        ]

def test_gtxn_xfer_asset():
    for i in GTXN_RANGE:
        expr = Gtxn.xfer_asset(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "XferAsset")
        ]

def test_gtxn_asset_amount():
    for i in GTXN_RANGE:
        expr = Gtxn.asset_amount(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "AssetAmount")
        ]

def test_gtxn_asset_sender():
    for i in GTXN_RANGE:
        expr = Gtxn.asset_sender(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "AssetSender")
        ]

def test_gtxn_asset_receiver():
    for i in GTXN_RANGE:
        expr = Gtxn.asset_receiver(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "AssetReceiver")
        ]

def test_gtxn_asset_close_to():
    for i in GTXN_RANGE:
        expr = Gtxn.asset_close_to(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "AssetCloseTo")
        ]

def test_gtxn_group_index():
    for i in GTXN_RANGE:
        expr = Gtxn.group_index(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "GroupIndex")
        ]

def test_gtxn_id():
    for i in GTXN_RANGE:
        expr = Gtxn.tx_id(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "TxID")
        ]

def test_txn_application_id():
    for i in GTXN_RANGE:
        expr = Gtxn.application_id(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ApplicationID")
        ]

def test_txn_on_completion():
    for i in GTXN_RANGE:
        expr = Gtxn.on_completion(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "OnCompletion")
        ]

def test_txn_application_args():
    for i in GTXN_RANGE:
        for j in range(4):
            expr = Gtxn.application_args(i)[j]
            assert expr.type_of() == TealType.bytes
            assert expr.__teal__() == [
                TealOp(Op.gtxna, i, "ApplicationArgs", j)
            ]

def test_txn_application_args_length():
    for i in GTXN_RANGE:
        expr = Gtxn.application_args(i).length()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "NumAppArgs")
        ]

def test_txn_accounts():
    for i in GTXN_RANGE:
        for j in range(4):
            expr = Gtxn.accounts(i)[j]
            assert expr.type_of() == TealType.bytes
            assert expr.__teal__() == [
                TealOp(Op.gtxna, i, "Accounts", j)
            ]

def test_txn_accounts_length():
    for i in GTXN_RANGE:
        expr = Gtxn.accounts(i).length()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "NumAccounts")
        ]

def test_txn_approval_program():
    for i in GTXN_RANGE:
        expr = Gtxn.approval_program(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ApprovalProgram")
        ]

def test_txn_clear_state_program():
    for i in GTXN_RANGE:
        expr = Gtxn.clear_state_program(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ClearStateProgram")
        ]

def test_txn_rekey_to():
    for i in GTXN_RANGE:
        expr = Gtxn.rekey_to(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "RekeyTo")
        ]

def test_txn_config_asset():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAsset")
        ]

def test_txn_config_asset_total():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset_total(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetTotal")
        ]

def test_txn_config_asset_decimals():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset_decimals(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetDecimals")
        ]

def test_txn_config_asset_default_frozen():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset_default_frozen(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetDefaultFrozen")
        ]

def test_txn_config_asset_unit_name():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset_unit_name(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetUnitName")
        ]

def test_txn_config_asset_name():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset_name(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetName")
        ]

def test_txn_config_asset_url():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset_url(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetURL")
        ]

def test_txn_config_asset_metadata_hash():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset_metadata_hash(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetMetadataHash")
        ]

def test_txn_config_asset_manager():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset_manager(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetManager")
        ]

def test_txn_config_asset_reserve():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset_reserve(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetReserve")
        ]

def test_txn_config_asset_freeze():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset_freeze(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetFreeze")
        ]

def test_txn_config_asset_clawback():
    for i in GTXN_RANGE:
        expr = Gtxn.config_asset_clawback(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetClawback")
        ]

def test_txn_freeze_asset():
    for i in GTXN_RANGE:
        expr = Gtxn.freeze_asset(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "FreezeAsset")
        ]

def test_txn_freeze_asset_account():
    for i in GTXN_RANGE:
        expr = Gtxn.freeze_asset_account(i)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "FreezeAssetAccount")
        ]

def test_txn_freeze_asset_frozen():
    for i in GTXN_RANGE:
        expr = Gtxn.freeze_asset_frozen(i)
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "FreezeAssetFrozen")
        ]

