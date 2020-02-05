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

def test_tmpl():
	Tmpl("TMPL_RECEIVER0")

	with pytest.raises(TealInputError):
		Tmpl("whatever")
		
def test_int():
    Int(232323)
    Int(Tmpl("TMPL_INT_MAX"))

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
    Bytes("base16", Tmpl("TMPL_SEC"))

    with pytest.raises(TealInputError):
        Bytes("base23", "")

    with pytest.raises(TealInputError):
        Bytes("base32", "Zm9vYmE=")

    with pytest.raises(TealInputError):
        Bytes("base64", "?????")

    with pytest.raises(TealInputError):
        Bytes("base16", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")


def test_or():
    p1 = Or(Int(1), Int(0))
    p2 = Int(1).Or(Int(0))
    assert p1.teal() == p2.teal()

    p3 = Or(Int(0), Int(1), Int(2))
    assert p3.__teal__() == \
        [['int', '0'], ['int', '1'], ['||'], ['int', '2'], ['||']]
    
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


def test_le():
    Int(1) <= Int(2)

    with pytest.raises(TealTypeError):
        Int(1) <= Txn.receiver()


def test_ge():
    Int(1) >= Int(1)

    with pytest.raises(TealTypeError):
        Int(1) >= Txn.receiver()
        
        
def test_eq():
    Eq(Int(2), Int(3))
    Eq(Txn.receiver(), Txn.sender())

    with pytest.raises(TealTypeMismatchError):
        Eq(Txn.fee(), Txn.receiver())


def test_arithmic():
    v = ((Int(2) + Int(3))/((Int(5) - Int(6)) * Int(8))) % Int(9)
    assert v.__teal__() == \
        [['int', '2'], ['int', '3'], ['+'], ['int', '5'], ['int', '6']] + \
        [['-'], ['int', '8'], ['*'], ['/'], ['int', '9'], ['%']]

    with pytest.raises(TealTypeError):
        Int(2) + Txn.receiver()

    with pytest.raises(TealTypeError):
        Int(2) - Txn.receiver()

    with pytest.raises(TealTypeError):
        Int(2) * Txn.receiver()

    with pytest.raises(TealTypeError):
        Int(2) / Txn.receiver()

    with pytest.raises(TealTypeError):
        Txn.receiver() % Int(2)
        

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
    Txn.lease()


def test_global():
    Global.min_txn_fee()
    Global.min_balance()
    Global.max_txn_life()
    Global.zero_address()
    Global.group_size()


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

    
def test_if():
    If(Int(0), Txn.sender(), Txn.receiver())

    with pytest.raises(TealTypeError):
        If(Int(0), Txn.amount(), Txn.sender())

    with pytest.raises(TealTypeError):
        If(Txn.sender(), Int(1), Int(0))

        
def test_itob():
    Itob(Int(1))

    with pytest.raises(TealTypeError):
        Itob(Arg(1))


def test_itob():
    Btoi(Arg(1))

    with pytest.raises(TealTypeError):
        Btoi(Int(1))


def test_nonce():
    Nonce("base32", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M", Int(1))
    Nonce("base32", "", Int(1))
    Nonce("base64", "Zm9vYmE=", Int(1))
    Nonce("base64", "", Int(1))
    Nonce("base16", "A21212EF", Int(1))
    Nonce("base16", "0xA21212EF", Int(1))
    Nonce("base16", "", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base23", "", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base32", "Zm9vYmE=", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base64", "?????", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base16", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M", Int(1))


def test_cond():
    Cond([Int(1), Int(2)], [Int(0), Int(2)])
    Cond([Int(1), Int(2)])
    Cond([Int(1), Int(2)], [Int(2), Int(3)], [Int(3), Int(4)])

    with pytest.raises(TealTypeError):
        Cond([Int(1), Int(2)],
             [Int(2), Txn.receiver()])

    with pytest.raises(TealTypeError):
        Cond([Arg(0), Int(2)])


def test_hashes():
    Sha256(Arg(0))
    Sha512_256(Arg(0))
    Keccak256(Arg(0))

    with pytest.raises(TealTypeError):
        Sha256(Int(1))

    with pytest.raises(TealTypeError):
        Sha512_256(Int(1))

    with pytest.raises(TealTypeError):
        Keccak256(Int(1))

