#!/usr/bin/env python3

from pyteal import *

""" Recurring Swap

This is a recurring payment contract. This contract can be set as an escrow 
and sending tmpl_amount recurringly to tmpl_rcv as long as secret is provided.

Use scenarios:
An insurer company set up this escrow contract and funded with Algos. 
Whenever the hospital received a record from the device, the hospital can send a 
transaction to transfer tmpl_amount of Algos from the escrow to the hospital. 
The hospital may be required to put some information about the record in the note 
field for audit purpose.

After timeout, the insurer can claw the remaining balance back.
"""

tmpl_rcv = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
tmpl_owner = Addr("7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
tmpl_amount = Int(500)
tmpl_fee = Int(1000)
tmpl_timeout = Int(100000)
# secret_hash: replace the value with the SHA256 value of the secret
tmpl_secret_hash = Bytes("base32", "23232323232323")

fee_cond = Txn.fee() <= tmpl_fee
type_cond = Txn.type_enum() == Int(1)
recv_cond = And(Txn.close_remainder_to() == Global.zero_address(),
                Txn.receiver() == tmpl_rcv,
                Sha256(Arg(0)) == tmpl_secret_hash)
close_cond = And(Txn.close_remainder_to() == tmpl_owner,
                 Txn.amount() == Int(0),
                 Txn.first_valid() >= tmpl_timeout)

recurring_swap = And(fee_cond, type_cond, Or(recv_cond, close_cond))
print(recurring_swap.teal())
