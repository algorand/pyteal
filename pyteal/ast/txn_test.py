import pytest

from .txn import *

def test_txn():
    Txn.sender()
    Txn.fee()
    Txn.first_valid()
    Txn.last_valid()
    Txn.note()
    Txn.receiver()
    Txn.amount()
    Txn.close_remainder_to()
    Txn.vote_pk()
    Txn.selection_pk()
    Txn.vote_first()
    Txn.vote_last()
    Txn.vote_key_dilution()
    Txn.type()
    Txn.type_enum()
    Txn.xfer_asset()
    Txn.asset_amount()
    Txn.asset_close_to()
    Txn.group_index()
    Txn.tx_id()
    Txn.lease()
