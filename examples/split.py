#!/usr/bin/env python3

from pyteal import *

"""Split
"""

# template variables
tmpl_fee = Int(1000)
tmpl_rcv1 = Addr("6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY")
tmpl_rcv2 = Addr("7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
tmpl_own = Addr("5MK5NGBRT5RL6IGUSYDIX5P7TNNZKRVXKT6FGVI6UVK6IZAWTYQGE4RZIQ")
tmpl_ratn  = Int(1)
tmpl_ratd = Int(3)
tmpl_min_pay = Int(1000)
tmpl_timeout = Int(3000)


split_core = (Txn.type_enum() == Int(1)).And(Txn.fee() < tmpl_fee)

split_transfer = And(Gtxn.sender(0) == Gtxn.sender(1),
                     Txn.close_remainder_to() == Global.zero_address(),
                     Gtxn.receiver(0) == tmpl_rcv1,
                     Gtxn.receiver(1) == tmpl_rcv2,
                     Gtxn.amount(0) == ((Gtxn.amount(0) + Gtxn.amount(1)) * tmpl_ratn) / tmpl_ratd,
                     Gtxn.amount(0) == tmpl_min_pay)

split_close = And(Txn.close_remainder_to() == tmpl_own,
                  Txn.receiver() == Global.zero_address(),
                  Txn.first_valid() == tmpl_timeout)

split = And(split_core,
            If(Global.group_size() == Int(2),
               split_transfer,
               split_close))

print(split.teal())
