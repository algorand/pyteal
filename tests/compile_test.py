#!/usr/bin/env python3

from pyteal import *

def test_atomic_swap():

    alice = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
    bob = Addr("7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
    secret = Bytes("base32", "23232323232323")

    fee_cond = Txn.fee() < Int(1000)
    type_cond = Txn.type_enum() == Int(1)
    recv_cond = (Txn.close_remainder_to() == Global.zero_address()).And(
        Txn.receiver() == alice).And(
        Arg(0) == secret)
    esc_cond = (Txn.close_remainder_to()  == Global.zero_address()).And(
        Txn.receiver() == bob).And(
        Txn.first_valid() > Int(3000))

    atomic_swap = fee_cond.And(type_cond).And(recv_cond.Or(esc_cond))

    a_teal = """txn Fee
int 1000
<
txn TypeEnum
int 1
=
&&
txn CloseRemainderTo
global ZeroAddress
=
txn Receiver
Addr 6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY
=
&&
arg 0
byte base32 23232323232323
=
&&
txn CloseRemainderTo
global ZeroAddress
=
txn Receiver
Addr 7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M
=
&&
txn FirstValid
int 3000
>
&&
||
&&"""
    assert atomic_swap.teal() == a_teal


def test_periodic_payment():
    tmpl_fee = Int(1000)
    tmpl_period = Int(50)
    tmpl_dur = Int(5000)
    tmpl_x = Bytes("base64", "023sdDE2")
    tmpl_amt = Int(2000)
    tmpl_rcv = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
    tmpl_timeout = Int(30000)

    periodic_pay_core = And(Txn.type_enum() == Int(1),
                            Txn.fee() < tmpl_fee,
                            Txn.first_valid() % tmpl_period == Int(0),
                            Txn.last_valid() == tmpl_dur + Txn.first_valid(),
                            Txn.lease() == tmpl_x)
                      
    periodic_pay_transfer = And(Txn.close_remainder_to() ==  Global.zero_address(),
                                Txn.receiver() == tmpl_rcv,
                                Txn.amount() == tmpl_amt)

    periodic_pay_close = And(Txn.close_remainder_to() == tmpl_rcv,
                             Txn.receiver() == Global.zero_address(),
                             Txn.first_valid() == tmpl_timeout,
                             Txn.amount() == Int(0))

    periodic_pay_escrow = periodic_pay_core.And(periodic_pay_transfer.Or(periodic_pay_close))

    p_teal = """txn TypeEnum
int 1
=
txn Fee
int 1000
<
&&
txn FirstValid
int 50
%
int 0
=
&&
txn LastValid
int 5000
txn FirstValid
+
=
&&
txn Lease
byte base64 023sdDE2
=
&&
txn CloseRemainderTo
global ZeroAddress
=
txn Receiver
Addr 6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY
=
&&
txn Amount
int 2000
=
&&
txn CloseRemainderTo
Addr 6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY
=
txn Receiver
global ZeroAddress
=
&&
txn FirstValid
int 30000
=
&&
txn Amount
int 0
=
&&
||
&&"""
    assert periodic_pay_escrow.teal() == p_teal

