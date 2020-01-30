#!/usr/bin/env python3

from pyteal import *

""" Atomic Swap
"""
alice = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
bob = Addr("7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
secret = Bytes("base32", "23232323232323")

fee_cond = Txn.fee() < Int(1000)
type_cond = Txn.type_enum() == Int(1)
recv_cond = (Txn.close_remainder_to() == Global.zero_address()).And(
             Txn.receiver() == alice).And(
             Sha256(Arg(0)) == secret)
esc_cond = (Txn.close_remainder_to()  == Global.zero_address()).And(
            Txn.receiver() == bob).And(
            Txn.first_valid() > Int(3000))

atomic_swap = fee_cond.And(type_cond).And(recv_cond.Or(esc_cond))   

print(atomic_swap.teal())
