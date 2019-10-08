#!/usr/bin/env python3

from pyteal import *

fee_cond = Txn.fee() < Int(300)
type_cond = Txn.type_enum() == Int(1)
recv_cond = (Txn.close_remainder_to() == Global.zero_address()).And(
             Txn.receiver() == Addr("0x2223223d23d33223")).And(
             Arg(0) == Bytes("base32", "23232323232323"))
esc_cond = (Txn.close_remainder_to()  == Global.zero_address()).And(
            Txn.receiver() == Addr("0x111111111111")).And(
            Txn.first_valid() > Int(300))
atomic_swap = fee_cond.And(type_cond).And(recv_cond.Or(esc_cond))   
print(atomic_swap.teal())
