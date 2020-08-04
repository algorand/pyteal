import pytest

from .. import *

def test_txn_sender():
    expr = Txn.sender()
    assert expr.__teal__() == [
        ["txn", "Sender"]
    ]

def test_txn_fee():
    expr = Txn.fee()
    assert expr.__teal__() == [
        ["txn", "Fee"]
    ]

def test_txn_first_valid():
    expr = Txn.first_valid()
    assert expr.__teal__() == [
        ["txn", "FirstValid"]
    ]

def test_txn_last_valid():
    expr = Txn.last_valid()
    assert expr.__teal__() == [
        ["txn", "LastValid"]
    ]

def test_txn_note():
    expr = Txn.note()
    assert expr.__teal__() == [
        ["txn", "Note"]
    ]

def test_txn_receiver():
    expr = Txn.receiver()
    assert expr.__teal__() == [
        ["txn", "Receiver"]
    ]

def test_txn_amount():
    expr = Txn.amount()
    assert expr.__teal__() == [
        ["txn", "Amount"]
    ]

def test_txn_close_remainder_to():
    expr = Txn.close_remainder_to()
    assert expr.__teal__() == [
        ["txn", "CloseRemainderTo"]
    ]

def test_txn_vote_pk():
    expr = Txn.vote_pk()
    assert expr.__teal__() == [
        ["txn", "VotePK"]
    ]

def test_txn_selection_pk():
    expr = Txn.selection_pk()
    assert expr.__teal__() == [
        ["txn", "SelectionPK"]
    ]

def test_txn_vote_first():
    expr = Txn.vote_first()
    assert expr.__teal__() == [
        ["txn", "VoteFirst"]
    ]

def test_txn_vote_last():
    expr = Txn.vote_last()
    assert expr.__teal__() == [
        ["txn", "VoteLast"]
    ]

def test_txn_vote_key_dilution():
    expr = Txn.vote_key_dilution()
    assert expr.__teal__() == [
        ["txn", "VoteKeyDilution"]
    ]

def test_txn_type():
    expr = Txn.type()
    assert expr.__teal__() == [
        ["txn", "Type"]
    ]

def test_txn_type_enum():
    expr = Txn.type_enum()
    assert expr.__teal__() == [
        ["txn", "TypeEnum"]
    ]

def test_txn_xfer_asset():
    expr = Txn.xfer_asset()
    assert expr.__teal__() == [
        ["txn", "XferAsset"]
    ]

def test_txn_asset_amount():
    expr = Txn.asset_amount()
    assert expr.__teal__() == [
        ["txn", "AssetAmount"]
    ]

def test_txn_asset_close_to():
    expr = Txn.asset_close_to()
    assert expr.__teal__() == [
        ["txn", "AssetCloseTo"]
    ]

def test_txn_group_index():
    expr = Txn.group_index()
    assert expr.__teal__() == [
        ["txn", "GroupIndex"]
    ]

def test_txn_id():
    expr = Txn.tx_id()
    assert expr.__teal__() == [
        ["txn", "TxID"]
    ]

def test_txn_lease():
    expr = Txn.lease()
    assert expr.__teal__() == [
        ["txn", "Lease"]
    ]
