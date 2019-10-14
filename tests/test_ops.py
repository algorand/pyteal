#!/usr/bin/env python3

import pytest

from pyteal import *

def test_addr():
    Addr("NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3THMF")

    with pytest.raises(TealInputError):
        Addr("NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3TH")

    with pytest.raises(TealInputError):
        Addr("000000000000000000000000000000000000000000000000000000000")

    with pytest.raises(TealInputError):
        Addr(2)


def test_int():
    Int(232323)

    with pytest.raises(TealInputError):
        Int(6.7)

    with pytest.raises(TealInputError):
        Int(-1)

    with pytest.raises(TealInputError):
        Int(2 ** 64)


def test_arg():
    Arg(0)

    with pytest.raises(TealInputError):
        Arg("k")

    with pytest.raises(TealInputError):
        Arg(-1)

    with pytest.raises(TealInputError):
        Arg(256)


def test_and():
    p1 = And(Int(1), Int(1))
    p2 = Int(1).And(Int(1))
    assert p1.teal() == p2.teal()

    p3 = And(Int(1), Int(1), Int(2))
    assert p3.__teal__() == \
    [['int', '1'], ['int', '1'], ['&&'], ['int', '2'], ['&&']]
    
    with pytest.raises(TealTypeError):
        And(Int(1), Txn.receiver())

    with pytest.raises(TealInputError):
        And(Int(1))
        

def test_bytes():
    Bytes("base32", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
    Bytes("base32", "")
    Bytes("base64", "Zm9vYmE=")
    Bytes("base64", "")
    Bytes("base16", "A21212EF")
    Bytes("base16", "0xA21212EF")
    Bytes("base16","")

    with pytest.raises(TealInputError):
        Bytes("base23", "")

    with pytest.raises(TealInputError):
        Bytes("base32", "Zm9vYmE=")

    with pytest.raises(TealInputError):
        Bytes("base64", "?????")

    with pytest.raises(TealInputError):
        Bytes("base16", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")


def test_or():
    Or(Int(1), Int(0))

    with pytest.raises(TealTypeError):
        Or(Int(1), Txn.receiver())


def test_lt():
    Lt(Int(2), Int(3))

    with pytest.raises(TealTypeError):
        Lt(Txn.fee(), Txn.receiver())

        
def test_gt():
    Gt(Int(2), Int(3))

    with pytest.raises(TealTypeError):
        Gt(Txn.fee(), Txn.receiver())


def test_eq():
    Eq(Int(2), Int(3))
    Eq(Txn.receiver(), Txn.sender())

    with pytest.raises(TealTypeMismatchError):
        Eq(Txn.fee(), Txn.receiver())


def test_len():
    Len(Txn.receiver())

    with pytest.raises(TealTypeError):
        Len(Int(1))


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
    Txn.sender_balance()
    Txn.lease()


def test_global():
    Global.round()
    Global.min_txn_fee()
    Global.min_balance()
    Global.max_txn_life()
    Global.time_stamp()
    Global.zero_address()
    Global.group_size()
