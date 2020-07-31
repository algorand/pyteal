import pytest

from .gtxn import *

def test_gtxn():

    with pytest.raises(TealInputError):
        Gtxn(-1, TxnField.fee)

    with pytest.raises(TealInputError):
        Gtxn(MAX_GROUP_SIZE+1, TxnField.sender)

    Gtxn.sender(0)
    Gtxn.fee(1)
    Gtxn.first_valid(1)
    Gtxn.last_valid(1)
    Gtxn.note(1)
    Gtxn.lease(1)
    Gtxn.receiver(1)
    Gtxn.amount(1)
    Gtxn.close_remainder_to(1)
    Gtxn.vote_pk(1)
    Gtxn.selection_pk(1)
    Gtxn.vote_first(1)
    Gtxn.vote_last(1)
    Gtxn.vote_key_dilution(1)
    Gtxn.type(1)
    Gtxn.type_enum(1)
    Gtxn.xfer_asset(1)
    Gtxn.asset_amount(1)
    Gtxn.asset_sender(1)
    Gtxn.asset_receiver(1)
    Gtxn.asset_close_to(1)
    Gtxn.group_index(1)
    Gtxn.tx_id(1)
