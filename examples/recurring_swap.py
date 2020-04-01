#!/usr/bin/env python3

from pyteal import *

""" Recurring Swap

This is a recurring payment contract. This contract can be set as an escrow 
and sending tmpl_amount recurringly to tmpl_rcv as long as secret is provided.

Use scenarios:
A insurer company set up this escrow contract and funded with Algos. 
Whenever the hospital received a record from the device, the hospital can send a 
transaction to transfer tmpl_amount of Algos from the escrow to the hospital. 
The hospital may be required to put some information about the record in the note 
field for audit purpose.

"""

tmpl_rcv = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
tmpl_amount = Int(500)
tmpl_fee = 1000
# secret_hash: replace the value with the SHA256 value of the secret
tmpl_secret_hash = Bytes("base32", "23232323232323")

fee_cond = Txn.fee() < Int(1000)
type_cond = Txn.type_enum() == Int(1)
recv_cond = And(Txn.close_remainder_to() == Global.zero_address(),
                Txn.receiver() == tmpl_rcv,
                Sha256(Arg(0)) == tmpl_secret_hash)

recurring_swap = And(fee_cond, type_cond, recv_cond)
print(recurring_swap.teal())
