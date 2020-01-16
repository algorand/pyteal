#!/usr/bin/env python3

from pyteal import *


""" Template for layer 1 dutch auction (from Fabrice and Shai)
"""

start_round = Tmpl("TMPL_START_ROUND")
start_price = Tmpl("TMPL_START_PRICE")
supply = Tmpl("TMPL_N")
price_decrement = Tmpl("TMPL_PRICE_INCREMENT")
period = Tmpl("TMPL_PERIOD")
asset_a = Tmpl("TMPL_ASSET_A")
asset_b = Tmpl("TMPL_ASSET_B")
asset_c = Tmpl("TMPL_ASSET_C")
asset_d = Tmpl("TMPL_ASSET_D")
receiver = Tmpl("TMPL_RECEIVER")
algo_sink = Tmpl("TMPL_ALGO_ZERO")
asset_a_sink = Tmpl("TMPL_A_ZERO")
asset_b_sink = Tmpl("TMPL_B_ZERO")
asset_c_sink = Tmpl("TMPL_C_ZERO")
asset_d_sink = Tmpl("TMPL_D_ZERO")
redeem_round = Tmpl("TMPL_REDEEM_ROUND")
wrapup_time = Tmpl("TMPL_WRAPUP_ROUND")

# the definition of i simplifies the original desgin by only constraining last_valid here
i_upper = (Gtxn.last_valid(0)- Int(start_round))/ Int(period)

bid = And(Gtxn.last_valid(0) == Gtxn.last_valid(1),
          Gtxn.last_valid(1) == Gtxn.last_valid(2),
          Gtxn.last_valid(2) == Gtxn.last_valid(3),
          Gtxn.last_valid(3) == Gtxn.last_valid(4),
          Gtxn.last_valid(4) < (Int(start_round) + i_upper * Int(period)),
          Gtxn.type_enum(0) == Int(4), # asset transfer
          Gtxn.xfer_asset(0) == Int(asset_d),
          Gtxn.receiver(0) == Addr(receiver),
          Gtxn.type_enum(1) == Int(4),
          Gtxn.xfer_asset(1) == Int(asset_b),
          Gtxn.type_enum(2) == Int(4),
          Gtxn.xfer_asset(2) == Int(asset_c),
          Gtxn.type_enum(3) == Int(4),
          Gtxn.xfer_asset(3) == Int(asset_c),
          Gtxn.type_enum(4) == Int(1),
          Gtxn.amount(4) == (Gtxn.fee(1) + Gtxn.fee(2) + Gtxn.fee(3)), #? why only 1, 2, 3
          Gtxn.asset_amount(0) == Gtxn.asset_amount(1),
          Gtxn.asset_amount(1) == Gtxn.asset_amount(2),
          Gtxn.asset_amount(3) == i_upper * Int(supply) * Int(price_decrement),
          Gtxn.sender(0) == Gtxn.receiver(1),
          Gtxn.receiver(2) == Addr(asset_c_sink),
          Gtxn.sender(1) == Gtxn.sender(2),
          Gtxn.sender(2) == Gtxn.sender(3),
          Gtxn.sender(3) == Gtxn.receiver(3),
          Gtxn.receiver(3) == Gtxn.receiver(4))

redeem = And(Gtxn.first_valid(0) == Gtxn.first_valid(1),
             Gtxn.first_valid(1) == Gtxn.first_valid(2),
             Gtxn.first_valid(2) == Gtxn.first_valid(3),
             Gtxn.first_valid(3) >= Int(redeem_round),
             Gtxn.type_enum(0) == Int(4),
             Gtxn.xfer_asset(0) == Int(asset_b),
             Gtxn.type_enum(1) == Int(4),
             Gtxn.xfer_asset(1) == Int(asset_a),
             Gtxn.type_enum(2) == Int(4),
             Gtxn.xfer_asset(2) == Int(asset_c),
             Gtxn.asset_amount(2) == Int(redeem_round) * Int(supply) * Int(price_decrement),
             Gtxn.type_enum(3) == Int(1),
             Gtxn.amount(3) == Gtxn.fee(1) + Gtxn.fee(2),
             Gtxn.asset_amount(1) ==
             Gtxn.asset_amount(0) * (Int(start_price) - Int(price_decrement) * Btoi(Arg(0))),
             Gtxn.sender(0) == Gtxn.receiver(1),
             Gtxn.receiver(0) == Gtxn.sender(1),
             Gtxn.sender(1) == Gtxn.sender(2),
             Gtxn.sender(2) == Gtxn.receiver(2),
             Gtxn.receiver(2) == Gtxn.receiver(3))
             
wrapup = And(Global.group_size() == Int(1),
             Txn.first_valid() >= Int(start_round) + Int(wrapup_time),
             Or(And(Txn.type_enum() == Int(1),
                    Txn.amount() == Int(0),
                    Txn.close_remainder_to() == Addr(receiver)),
                And(Txn.type_enum() == Int(4),
                    Txn.asset_amount() == Int(0),
                    Txn.asset_close_to() == Addr(receiver),
                    Txn.xfer_asset() == Int(asset_a))))


dutch = Cond([Global.group_size() == Int(5), bid],
             [Global.group_size() == Int(4), redeem],
             [Global.group_size() == Int(1), wrapup])

print(dutch.teal())
