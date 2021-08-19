# This example is provided for informational purposes only and has not been audited for security.

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
tmpl_amount = Int(100000)
tmpl_fee = Int(1000)
tmpl_timeout = Int(100000)


def recurring_swap(
    tmpl_buyer=tmpl_buyer,
    tmpl_provider=tmpl_provider,
    tmpl_amount=tmpl_amount,
    tmpl_fee=tmpl_fee,
    tmpl_timeout=tmpl_timeout,
):
    fee_cond = Txn.fee() <= tmpl_fee
    type_cond = And(Txn.type_enum() == Int(1), Txn.rekey_to() == Global.zero_address())
    recv_cond = And(
        Txn.close_remainder_to() == Global.zero_address(),
        Txn.receiver() == tmpl_provider,
        Txn.amount() == tmpl_amount,
        Ed25519Verify(Itob(Txn.first_valid()), Arg(0), tmpl_provider),
        Txn.lease() == Sha256(Itob(Txn.first_valid())),
    )

    close_cond = And(
        Txn.close_remainder_to() == tmpl_buyer,
        Txn.amount() == Int(0),
        Txn.first_valid() >= tmpl_timeout,
    )

    program = And(fee_cond, type_cond, Or(recv_cond, close_cond))

    return program


if __name__ == "__main__":
    print(compileTeal(recurring_swap(), mode=Mode.Signature, version=2))
