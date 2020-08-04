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
        assert expr.__teal__() == [
            ["gtxn", str(i), "Sender"]
        ]

def test_gtxn_fee():
    for i in GTXN_RANGE:
        expr = Gtxn.fee(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "Fee"]
        ]

def test_gtxn_first_valid():
    for i in GTXN_RANGE:
        expr = Gtxn.first_valid(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "FirstValid"]
        ]

def test_gtxn_last_valid():
    for i in GTXN_RANGE:
        expr = Gtxn.last_valid(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "LastValid"]
        ]

def test_gtxn_note():
    for i in GTXN_RANGE:
        expr = Gtxn.note(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "Note"]
        ]

def test_gtxn_receiver():
    for i in GTXN_RANGE:
        expr = Gtxn.receiver(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "Receiver"]
        ]

def test_gtxn_amount():
    for i in GTXN_RANGE:
        expr = Gtxn.amount(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "Amount"]
        ]

def test_gtxn_close_remainder_to():
    for i in GTXN_RANGE:
        expr = Gtxn.close_remainder_to(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "CloseRemainderTo"]
        ]

def test_gtxn_vote_pk():
    for i in GTXN_RANGE:
        expr = Gtxn.vote_pk(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "VotePK"]
        ]

def test_gtxn_selection_pk():
    for i in GTXN_RANGE:
        expr = Gtxn.selection_pk(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "SelectionPK"]
        ]

def test_gtxn_vote_first():
    for i in GTXN_RANGE:
        expr = Gtxn.vote_first(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "VoteFirst"]
        ]

def test_gtxn_vote_last():
    for i in GTXN_RANGE:
        expr = Gtxn.vote_last(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "VoteLast"]
        ]

def test_gtxn_vote_key_dilution():
    for i in GTXN_RANGE:
        expr = Gtxn.vote_key_dilution(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "VoteKeyDilution"]
        ]

def test_gtxn_type():
    for i in GTXN_RANGE:
        expr = Gtxn.type(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "Type"]
        ]

def test_gtxn_type_enum():
    for i in GTXN_RANGE:
        expr = Gtxn.type_enum(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "TypeEnum"]
        ]

def test_gtxn_xfer_asset():
    for i in GTXN_RANGE:
        expr = Gtxn.xfer_asset(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "XferAsset"]
        ]

def test_gtxn_asset_amount():
    for i in GTXN_RANGE:
        expr = Gtxn.asset_amount(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "AssetAmount"]
        ]

def test_gtxn_asset_close_to():
    for i in GTXN_RANGE:
        expr = Gtxn.asset_close_to(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "AssetCloseTo"]
        ]

def test_gtxn_group_index():
    for i in GTXN_RANGE:
        expr = Gtxn.group_index(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "GroupIndex"]
        ]

def test_gtxn_id():
    for i in GTXN_RANGE:
        expr = Gtxn.tx_id(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "TxID"]
        ]

def test_gtxn_lease():
    for i in GTXN_RANGE:
        expr = Gtxn.lease(i)
        assert expr.__teal__() == [
            ["gtxn", str(i), "Lease"]
        ]
