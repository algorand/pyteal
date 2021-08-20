# This example is provided for informational purposes only and has not been audited for security.

from pyteal import *

"""Periodic Payment"""

tmpl_fee = Int(1000)
tmpl_period = Int(50)
tmpl_dur = Int(5000)
tmpl_lease = Bytes("base64", "023sdDE2")
tmpl_amt = Int(2000)
tmpl_rcv = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
tmpl_timeout = Int(30000)


def periodic_payment(
    tmpl_fee=tmpl_fee,
    tmpl_period=tmpl_period,
    tmpl_dur=tmpl_dur,
    tmpl_lease=tmpl_lease,
    tmpl_amt=tmpl_amt,
    tmpl_rcv=tmpl_rcv,
    tmpl_timeout=tmpl_timeout,
):

    periodic_pay_core = And(
        Txn.type_enum() == TxnType.Payment,
        Txn.fee() < tmpl_fee,
        Txn.first_valid() % tmpl_period == Int(0),
        Txn.last_valid() == tmpl_dur + Txn.first_valid(),
        Txn.lease() == tmpl_lease,
    )

    periodic_pay_transfer = And(
        Txn.close_remainder_to() == Global.zero_address(),
        Txn.rekey_to() == Global.zero_address(),
        Txn.receiver() == tmpl_rcv,
        Txn.amount() == tmpl_amt,
    )

    periodic_pay_close = And(
        Txn.close_remainder_to() == tmpl_rcv,
        Txn.rekey_to() == Global.zero_address(),
        Txn.receiver() == Global.zero_address(),
        Txn.first_valid() == tmpl_timeout,
        Txn.amount() == Int(0),
    )

    periodic_pay_escrow = periodic_pay_core.And(
        periodic_pay_transfer.Or(periodic_pay_close)
    )

    return periodic_pay_escrow


if __name__ == "__main__":
    print(compileTeal(periodic_payment(), mode=Mode.Signature, version=2))
