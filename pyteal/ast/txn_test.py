import pytest

from .. import *

def test_txn_sender():
    expr = Txn.sender()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "Sender")
    ]

def test_txn_fee():
    expr = Txn.fee()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "Fee")
    ]

def test_txn_first_valid():
    expr = Txn.first_valid()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "FirstValid")
    ]

def test_txn_last_valid():
    expr = Txn.last_valid()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "LastValid")
    ]

def test_txn_note():
    expr = Txn.note()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "Note")
    ]

def test_txn_lease():
    expr = Txn.lease()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "Lease")
    ]

def test_txn_receiver():
    expr = Txn.receiver()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "Receiver")
    ]

def test_txn_amount():
    expr = Txn.amount()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "Amount")
    ]

def test_txn_close_remainder_to():
    expr = Txn.close_remainder_to()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "CloseRemainderTo")
    ]

def test_txn_vote_pk():
    expr = Txn.vote_pk()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "VotePK")
    ]

def test_txn_selection_pk():
    expr = Txn.selection_pk()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "SelectionPK")
    ]

def test_txn_vote_first():
    expr = Txn.vote_first()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "VoteFirst")
    ]

def test_txn_vote_last():
    expr = Txn.vote_last()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "VoteLast")
    ]

def test_txn_vote_key_dilution():
    expr = Txn.vote_key_dilution()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "VoteKeyDilution")
    ]

def test_txn_type():
    expr = Txn.type()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "Type")
    ]

def test_txn_type_enum():
    expr = Txn.type_enum()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "TypeEnum")
    ]

def test_txn_xfer_asset():
    expr = Txn.xfer_asset()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "XferAsset")
    ]

def test_txn_asset_amount():
    expr = Txn.asset_amount()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "AssetAmount")
    ]

def test_txn_asset_sender():
    expr = Txn.asset_sender()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "AssetSender")
    ]

def test_txn_asset_receiver():
    expr = Txn.asset_receiver()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "AssetReceiver")
    ]

def test_txn_asset_close_to():
    expr = Txn.asset_close_to()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "AssetCloseTo")
    ]

def test_txn_group_index():
    expr = Txn.group_index()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "GroupIndex")
    ]

def test_txn_id():
    expr = Txn.tx_id()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "TxID")
    ]

def test_txn_application_id():
    expr = Txn.application_id()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "ApplicationID")
    ]

def test_txn_on_completion():
    expr = Txn.on_completion()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "OnCompletion")
    ]

def test_txn_application_args():
    for i in range(4):
        expr = Txn.application_args[i]
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.txna, "ApplicationArgs", i)
        ]

def test_txn_application_args_length():
    expr = Txn.application_args.length()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "NumAppArgs")
    ]

def test_txn_accounts():
    for i in range(4):
        expr = Txn.accounts[i]
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.txna, "Accounts", i)
        ]

def test_txn_accounts_length():
    expr = Txn.accounts.length()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "NumAccounts")
    ]

def test_txn_approval_program():
    expr = Txn.approval_program()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "ApprovalProgram")
    ]

def test_txn_clear_state_program():
    expr = Txn.clear_state_program()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "ClearStateProgram")
    ]

def test_txn_rekey_to():
    expr = Txn.rekey_to()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "RekeyTo")
    ]

def test_txn_config_asset():
    expr = Txn.config_asset()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAsset")
    ]

def test_txn_config_asset_total():
    expr = Txn.config_asset_total()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAssetTotal")
    ]

def test_txn_config_asset_decimals():
    expr = Txn.config_asset_decimals()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAssetDecimals")
    ]

def test_txn_config_asset_default_frozen():
    expr = Txn.config_asset_default_frozen()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAssetDefaultFrozen")
    ]

def test_txn_config_asset_unit_name():
    expr = Txn.config_asset_unit_name()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAssetUnitName")
    ]

def test_txn_config_asset_name():
    expr = Txn.config_asset_name()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAssetName")
    ]

def test_txn_config_asset_url():
    expr = Txn.config_asset_url()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAssetURL")
    ]

def test_txn_config_asset_metadata_hash():
    expr = Txn.config_asset_metadata_hash()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAssetMetadataHash")
    ]

def test_txn_config_asset_manager():
    expr = Txn.config_asset_manager()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAssetManager")
    ]

def test_txn_config_asset_reserve():
    expr = Txn.config_asset_reserve()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAssetReserve")
    ]

def test_txn_config_asset_freeze():
    expr = Txn.config_asset_freeze()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAssetFreeze")
    ]

def test_txn_config_asset_clawback():
    expr = Txn.config_asset_clawback()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "ConfigAssetClawback")
    ]

def test_txn_freeze_asset():
    expr = Txn.freeze_asset()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "FreezeAsset")
    ]

def test_txn_freeze_asset_account():
    expr = Txn.freeze_asset_account()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.txn, "FreezeAssetAccount")
    ]

def test_txn_freeze_asset_frozen():
    expr = Txn.freeze_asset_frozen()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "FreezeAssetFrozen")
    ]
