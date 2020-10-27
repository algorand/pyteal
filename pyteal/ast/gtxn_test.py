import pytest

from .. import *
# this is not necessary but mypy complains if it's not included
from .. import MAX_GROUP_SIZE

GTXN_RANGE = range(MAX_GROUP_SIZE)

def test_gtxn_invalid():
    with pytest.raises(TealInputError):
        Gtxn[-1].fee()

    with pytest.raises(TealInputError):
        Gtxn[MAX_GROUP_SIZE+1].sender()

def test_gtxn_sender():
    for i in GTXN_RANGE:
        expr = Gtxn[i].sender()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Sender")
        ]

def test_gtxn_fee():
    for i in GTXN_RANGE:
        expr = Gtxn[i].fee()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Fee")
        ]

def test_gtxn_first_valid():
    for i in GTXN_RANGE:
        expr = Gtxn[i].first_valid()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "FirstValid")
        ]

def test_gtxn_last_valid():
    for i in GTXN_RANGE:
        expr = Gtxn[i].last_valid()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "LastValid")
        ]

def test_gtxn_note():
    for i in GTXN_RANGE:
        expr = Gtxn[i].note()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Note")
        ]

def test_gtxn_lease():
    for i in GTXN_RANGE:
        expr = Gtxn[i].lease()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Lease")
        ]

def test_gtxn_receiver():
    for i in GTXN_RANGE:
        expr = Gtxn[i].receiver()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Receiver")
        ]

def test_gtxn_amount():
    for i in GTXN_RANGE:
        expr = Gtxn[i].amount()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Amount")
        ]

def test_gtxn_close_remainder_to():
    for i in GTXN_RANGE:
        expr = Gtxn[i].close_remainder_to()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "CloseRemainderTo")
        ]

def test_gtxn_vote_pk():
    for i in GTXN_RANGE:
        expr = Gtxn[i].vote_pk()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "VotePK")
        ]

def test_gtxn_selection_pk():
    for i in GTXN_RANGE:
        expr = Gtxn[i].selection_pk()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "SelectionPK")
        ]

def test_gtxn_vote_first():
    for i in GTXN_RANGE:
        expr = Gtxn[i].vote_first()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "VoteFirst")
        ]

def test_gtxn_vote_last():
    for i in GTXN_RANGE:
        expr = Gtxn[i].vote_last()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "VoteLast")
        ]

def test_gtxn_vote_key_dilution():
    for i in GTXN_RANGE:
        expr = Gtxn[i].vote_key_dilution()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "VoteKeyDilution")
        ]

def test_gtxn_type():
    for i in GTXN_RANGE:
        expr = Gtxn[i].type()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "Type")
        ]

def test_gtxn_type_enum():
    for i in GTXN_RANGE:
        expr = Gtxn[i].type_enum()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "TypeEnum")
        ]

def test_gtxn_xfer_asset():
    for i in GTXN_RANGE:
        expr = Gtxn[i].xfer_asset()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "XferAsset")
        ]

def test_gtxn_asset_amount():
    for i in GTXN_RANGE:
        expr = Gtxn[i].asset_amount()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "AssetAmount")
        ]

def test_gtxn_asset_sender():
    for i in GTXN_RANGE:
        expr = Gtxn[i].asset_sender()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "AssetSender")
        ]

def test_gtxn_asset_receiver():
    for i in GTXN_RANGE:
        expr = Gtxn[i].asset_receiver()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "AssetReceiver")
        ]

def test_gtxn_asset_close_to():
    for i in GTXN_RANGE:
        expr = Gtxn[i].asset_close_to()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "AssetCloseTo")
        ]

def test_gtxn_group_index():
    for i in GTXN_RANGE:
        expr = Gtxn[i].group_index()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "GroupIndex")
        ]

def test_gtxn_id():
    for i in GTXN_RANGE:
        expr = Gtxn[i].tx_id()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "TxID")
        ]

def test_txn_application_id():
    for i in GTXN_RANGE:
        expr = Gtxn[i].application_id()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ApplicationID")
        ]

def test_txn_on_completion():
    for i in GTXN_RANGE:
        expr = Gtxn[i].on_completion()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "OnCompletion")
        ]

def test_txn_application_args():
    for i in GTXN_RANGE:
        for j in range(4):
            expr = Gtxn[i].application_args[j]
            assert expr.type_of() == TealType.bytes
            assert expr.__teal__() == [
                TealOp(Op.gtxna, i, "ApplicationArgs", j)
            ]

def test_txn_application_args_length():
    for i in GTXN_RANGE:
        expr = Gtxn[i].application_args.length()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "NumAppArgs")
        ]

def test_txn_accounts():
    for i in GTXN_RANGE:
        for j in range(4):
            expr = Gtxn[i].accounts[j]
            assert expr.type_of() == TealType.bytes
            assert expr.__teal__() == [
                TealOp(Op.gtxna, i, "Accounts", j)
            ]

def test_txn_accounts_length():
    for i in GTXN_RANGE:
        expr = Gtxn[i].accounts.length()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "NumAccounts")
        ]

def test_txn_approval_program():
    for i in GTXN_RANGE:
        expr = Gtxn[i].approval_program()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ApprovalProgram")
        ]

def test_txn_clear_state_program():
    for i in GTXN_RANGE:
        expr = Gtxn[i].clear_state_program()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ClearStateProgram")
        ]

def test_txn_rekey_to():
    for i in GTXN_RANGE:
        expr = Gtxn[i].rekey_to()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "RekeyTo")
        ]

def test_txn_config_asset():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAsset")
        ]

def test_txn_config_asset_total():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_total()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetTotal")
        ]

def test_txn_config_asset_decimals():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_decimals()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetDecimals")
        ]

def test_txn_config_asset_default_frozen():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_default_frozen()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetDefaultFrozen")
        ]

def test_txn_config_asset_unit_name():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_unit_name()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetUnitName")
        ]

def test_txn_config_asset_name():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_name()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetName")
        ]

def test_txn_config_asset_url():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_url()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetURL")
        ]

def test_txn_config_asset_metadata_hash():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_metadata_hash()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetMetadataHash")
        ]

def test_txn_config_asset_manager():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_manager()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetManager")
        ]

def test_txn_config_asset_reserve():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_reserve()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetReserve")
        ]

def test_txn_config_asset_freeze():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_freeze()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetFreeze")
        ]

def test_txn_config_asset_clawback():
    for i in GTXN_RANGE:
        expr = Gtxn[i].config_asset_clawback()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "ConfigAssetClawback")
        ]

def test_txn_freeze_asset():
    for i in GTXN_RANGE:
        expr = Gtxn[i].freeze_asset()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "FreezeAsset")
        ]

def test_txn_freeze_asset_account():
    for i in GTXN_RANGE:
        expr = Gtxn[i].freeze_asset_account()
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "FreezeAssetAccount")
        ]

def test_txn_freeze_asset_frozen():
    for i in GTXN_RANGE:
        expr = Gtxn[i].freeze_asset_frozen()
        assert expr.type_of() == TealType.uint64
        assert expr.__teal__() == [
            TealOp(Op.gtxn, i, "FreezeAssetFrozen")
        ]

