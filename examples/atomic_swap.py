# This example is provided for informational purposes only and has not been audited for security.

from pyteal import *

"""Atomic Swap"""

alice = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
bob = Addr("7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
secret = Bytes("base32", "23232323232323")
timeout = 3000

def htlc(tmpl_seller=alice,
         tmpl_buyer=bob,
         tmpl_fee=1000,
         tmpl_secret=secret,
         tmpl_hash_fn=Sha256,
         tmpl_timeout=timeout):
    
    fee_cond = Txn.fee() < Int(tmpl_fee)
    type_cond = Txn.type_enum() == TxnType.Payment

    recv_cond = And(
        Txn.close_remainder_to() == Global.zero_address(),
        Txn.receiver() == tmpl_seller,
        tmpl_hash_fn(Arg(0)) == tmpl_secret
    )
    
    esc_cond = And(
        Txn.close_remainder_to() == Global.zero_address(),
        Txn.receiver() == tmpl_buyer,
        Txn.first_valid() > Int(tmpl_timeout)
    )

    return And(
        fee_cond,
        type_cond,
        Or(recv_cond, esc_cond)
    )

if __name__ == "__main__":
    print(compileTeal(htlc(), Mode.Signature))
