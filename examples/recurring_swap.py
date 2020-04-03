#!/usr/bin/env python3

from pyteal import *

""" Recurring Swap

This is a recurring swap contract. This contract can be set as an escrow 
and sending tmpl_amount recurringly to tmpl_provider as long as the transaction is authoried
by the provider.

Use scenarios:
A buyer (an insurer, for example) set up this escrow contract and funded with Algos. 
Whenever a service provider (a hospital, for example) authorize a payment,
it submits a transaction with its signature of first_valid in the arguement and with
the first_valid in the lease to prevent replay attacks.

The hospital may some extra information about the transaction in the note 
field for audit purpose.

After timeout, the buyer can claw the remaining balance back.
tmpl_buyer: buyer who receives the service
tmpl_provider: provider of the service
tmpl_ppk: public key of the provider
tmpl_amount: the amount of microAlgo charged per service
tmpl_fee: maximum transaction fee allowed
tmpl_timeout: the timeout round, after which the buyer can reclaim her Algos
"""

tmpl_buyer = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
tmpl_provider = Addr("7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
tmpl_ppk = Byte("base32", "GFFQ47565WX6VEIJXXIB4W5JNOS2UODKPASUO5T3N3RXLSBR2CEA")
tmpl_amount = Int(500)
tmpl_fee = Int(1000)
tmpl_timeout = Int(100000)

fee_cond = Txn.fee() <= tmpl_fee
type_cond = Txn.type_enum() == Int(1)
recv_cond = And(Txn.close_remainder_to() == Global.zero_address(),
                Txn.receiver() == tmpl_provider,
                Txn.amount() == tmpl_amount,
                Ed25519Verify(Itob(Txn.first_valid()), Arg(0), tmpl_ppk),
                Txn.lease() == Itob(Txn.first_valid()))
                
close_cond = And(Txn.close_remainder_to() == tmpl_buyer,
                 Txn.amount() == Int(0),
                 Txn.first_valid() >= tmpl_timeout)

recurring_swap = And(fee_cond, type_cond, Or(recv_cond, close_cond))
print(recurring_swap.teal())
