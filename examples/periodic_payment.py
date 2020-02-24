#!/usr/bin/env python3

from pyteal import *

#template variables
tmpl_fee = Int(1000)
tmpl_period = Int(1000)
tmpl_dur = Int(1000)
tmpl_x = Bytes("base64", "y9OJ5MRLCHQj8GqbikAUKMBI7hom+SOj8dlopNdNHXI=")
tmpl_amt = Int(2000)
tmpl_rcv = Addr("ZZAF5ARA4MEC5PVDOP64JM5O5MQST63Q2KOY2FLYFLXXD3PFSNJJBYAFZM")
tmpl_timeout = Int(300000)

periodic_pay_core = And(Txn.type_enum() == Int(1),
                        Txn.fee() <= tmpl_fee)
                      
periodic_pay_transfer = And(Txn.close_remainder_to() ==  Global.zero_address(),
                            Txn.receiver() == tmpl_rcv,
                            Txn.amount() == tmpl_amt,
                            Txn.first_valid() % tmpl_period == Int(0),
                            Txn.last_valid() == tmpl_dur + Txn.first_valid(),
                            Txn.lease() == tmpl_x)

periodic_pay_close = And(Txn.close_remainder_to() == tmpl_rcv,
                         Txn.receiver() == Global.zero_address(),
                         Txn.first_valid() >= tmpl_timeout,
                         Txn.amount() == Int(0))

periodic_pay_escrow = And(periodic_pay_core, Or(periodic_pay_transfer, periodic_pay_close))

print(periodic_pay_escrow.teal())
