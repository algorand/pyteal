#!/usr/bin/env python3

from pyteal import *
from pyteal.util import reset_label_count

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

    a_teal = """#pragma version 2
txn Fee
int 1000
<
txn TypeEnum
int 1
==
&&
txn CloseRemainderTo
global ZeroAddress
==
txn Receiver
addr 6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY
==
&&
arg 0
byte base32(23232323232323)
==
&&
txn CloseRemainderTo
global ZeroAddress
==
txn Receiver
addr 7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M
==
&&
txn FirstValid
int 3000
>
&&
||
&&"""
    reset_label_count()
    assert compileTeal(atomic_swap, Mode.Signature) == a_teal


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

    p_teal = """#pragma version 2
txn TypeEnum
int 1
==
txn Fee
int 1000
<
&&
txn FirstValid
int 50
%
int 0
==
&&
txn LastValid
int 5000
txn FirstValid
+
==
&&
txn Lease
byte base64(023sdDE2)
==
&&
txn CloseRemainderTo
global ZeroAddress
==
txn Receiver
addr 6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY
==
&&
txn Amount
int 2000
==
&&
txn CloseRemainderTo
addr 6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY
==
txn Receiver
global ZeroAddress
==
&&
txn FirstValid
int 30000
==
&&
txn Amount
int 0
==
&&
||
&&"""
    reset_label_count()
    assert compileTeal(periodic_pay_escrow, Mode.Signature) == p_teal


def test_split():
    # https://github.com/derbear/steal/blob/master/examples/split.rkt
    tmpl_rcv1 = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
    tmpl_rcv2 = Addr("7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")    
    tmpl_ratn = Int(32)
    tmpl_ratd = Int(68)
    tmpl_minpay = Int(5000000)
    tmpl_timeout = Int(30000)
    tmpl_own = Addr("SXOUGKH6RM5SO5A2JAZ5LR3CRM2JWL4LPQDCNRQO2IMLIMEH6T4QWKOREE")
    tmpl_fee = Int(1000)

    split_core = And(Txn.type_enum() == Int(1),
                     Txn.fee() < tmpl_fee)

    split_transfer = And(Gtxn[0].sender() == Gtxn[1].sender(),
                         Txn.close_remainder_to() == Global.zero_address(),
                         Gtxn[0].receiver() == tmpl_rcv1,
                         Gtxn[1].receiver() == tmpl_rcv2,
                         Gtxn[1].amount() == ((Gtxn[0].amount() + Gtxn[1].amount()) * tmpl_ratn) / tmpl_ratd,
                         Gtxn[0].amount() == tmpl_minpay)

    split_close = And(Txn.close_remainder_to() == tmpl_own,
                      Txn.receiver() == Global.zero_address(),
                      Txn.amount() == Int(0),
                      Txn.first_valid() > tmpl_timeout)

    split = And(split_core,
                If(Global.group_size() == Int(2),
                   split_transfer,
                   split_close))

    target = """#pragma version 2
txn TypeEnum
int 1
==
txn Fee
int 1000
<
&&
global GroupSize
int 2
==
bnz l0
txn CloseRemainderTo
addr SXOUGKH6RM5SO5A2JAZ5LR3CRM2JWL4LPQDCNRQO2IMLIMEH6T4QWKOREE
==
txn Receiver
global ZeroAddress
==
&&
txn Amount
int 0
==
&&
txn FirstValid
int 30000
>
&&
b l1
l0:
gtxn 0 Sender
gtxn 1 Sender
==
txn CloseRemainderTo
global ZeroAddress
==
&&
gtxn 0 Receiver
addr 6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY
==
&&
gtxn 1 Receiver
addr 7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M
==
&&
gtxn 1 Amount
gtxn 0 Amount
gtxn 1 Amount
+
int 32
*
int 68
/
==
&&
gtxn 0 Amount
int 5000000
==
&&
l1:
&&"""
    reset_label_count()
    assert compileTeal(split, Mode.Signature) == target


def test_cond():
	cond1 = Txn.fee() < Int(2000)
	cond2 = Txn.amount() > Int(5000)
	cond3 = Txn.receiver() == Txn.sender()
	core = Cond([Global.group_size()==Int(2), cond1],
				[Global.group_size()==Int(3), cond2],
				[Global.group_size()==Int(4), cond3])
	compileTeal(core, Mode.Signature)
