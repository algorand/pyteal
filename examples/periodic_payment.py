#!/usr/bin/env python3

from pyteal import *

#template variables
tmpl_fee = Int(1000)
tmpl_period = Int(1000)
tmpl_dur = Int(1000)
tmpl_lease = Bytes("base64", "y9OJ5MRLCHQj8GqbikAUKMBI7hom+SOj8dlopNdNHXI=")
tmpl_amt = Int(200000)
tmpl_rcv = Addr("ZZAF5ARA4MEC5PVDOP64JM5O5MQST63Q2KOY2FLYFLXXD3PFSNJJBYAFZM")

def periodic_payment(tmpl_fee=tmpl_fee,
                     tmpl_period=tmpl_period,
                     tmpl_dur=tmpl_dur,
                     tmpl_lease=tmpl_lease,
                     tmpl_amt=tmpl_amt,
                     tmpl_rcv=tmpl_rcv):

    periodic_pay_core = And(Txn.type_enum() == Int(1),
                            Txn.fee() <= tmpl_fee)
    
    periodic_pay_transfer = And(Txn.close_remainder_to() ==  Global.zero_address(),
                                Txn.receiver() == tmpl_rcv,
                                Txn.amount() == tmpl_amt,
                                Txn.first_valid() % tmpl_period == Int(0),
                                Txn.last_valid() == tmpl_dur + Txn.first_valid(),
                                Txn.lease() == tmpl_lease)

    return And(periodic_pay_core, periodic_pay_transfer)

# print(periodic_payment().teal())
