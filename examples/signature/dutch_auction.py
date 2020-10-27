# This example is provided for informational purposes only and has not been audited for security.

from pyteal import *


""" Template for layer 1 dutch auction (from Fabrice and Shai)
"""

start_round = Tmpl.Int("TMPL_START_ROUND")
start_price = Tmpl.Int("TMPL_START_PRICE")
supply = Tmpl.Int("TMPL_N")
price_decrement = Tmpl.Int("TMPL_PRICE_INCREMENT")
period = Tmpl.Int("TMPL_PERIOD")
asset_a = Tmpl.Int("TMPL_ASSET_A")
asset_b = Tmpl.Int("TMPL_ASSET_B")
asset_c = Tmpl.Int("TMPL_ASSET_C")
asset_d = Tmpl.Int("TMPL_ASSET_D")
receiver = Tmpl.Addr("TMPL_RECEIVER")
algo_sink = Tmpl.Addr("TMPL_ALGO_ZERO")
asset_a_sink = Tmpl.Addr("TMPL_A_ZERO")
asset_b_sink = Tmpl.Addr("TMPL_B_ZERO")
asset_c_sink = Tmpl.Addr("TMPL_C_ZERO")
asset_d_sink = Tmpl.Addr("TMPL_D_ZERO")
redeem_round = Tmpl.Int("TMPL_REDEEM_ROUND")
wrapup_time = Tmpl.Int("TMPL_WRAPUP_ROUND")

# the definition of i simplifies the original desgin by only constraining last_valid here
i_upper = (Gtxn[0].last_valid()- start_round)/ period

bid = And(Gtxn[0].last_valid() == Gtxn[1].last_valid(),
          Gtxn[1].last_valid() == Gtxn[2].last_valid(),
          Gtxn[2].last_valid() == Gtxn[3].last_valid(),
          Gtxn[3].last_valid() == Gtxn[4].last_valid(),
          Gtxn[4].last_valid() < (start_round + i_upper * period),
          Gtxn[0].type_enum() == Int(4), # asset transfer
          Gtxn[0].xfer_asset() == asset_d,
          Gtxn[0].receiver() == receiver,
          Gtxn[1].type_enum() == Int(4),
          Gtxn[1].xfer_asset() == asset_b,
          Gtxn[2].type_enum() == Int(4),
          Gtxn[2].xfer_asset() == asset_c,
          Gtxn[3].type_enum() == Int(4),
          Gtxn[4].xfer_asset() == asset_c,
          Gtxn[4].type_enum() == Int(1),
          Gtxn[4].amount() == (Gtxn[1].fee() + Gtxn[2].fee() + Gtxn[3].fee()), #? why only 1, 2, 3
          Gtxn[0].asset_amount() == Gtxn[1].asset_amount(),
          Gtxn[1].asset_amount() == Gtxn[2].asset_amount(),
          Gtxn[3].asset_amount() == i_upper * supply * price_decrement,
          Gtxn[0].sender() == Gtxn[1].receiver(),
          Gtxn[2].receiver() == asset_c_sink,
          Gtxn[1].sender() == Gtxn[2].sender(),
          Gtxn[2].sender() == Gtxn[3].sender(),
          Gtxn[3].sender() == Gtxn[3].receiver(),
          Gtxn[3].receiver() == Gtxn[4].receiver())

redeem = And(Gtxn[0].first_valid() == Gtxn[1].first_valid(),
             Gtxn[1].first_valid() == Gtxn[2].first_valid(),
             Gtxn[2].first_valid() == Gtxn[3].first_valid(),
             Gtxn[3].first_valid() >= redeem_round,
             Gtxn[0].type_enum() == Int(4),
             Gtxn[0].xfer_asset() == asset_b,
             Gtxn[1].type_enum() == Int(4),
             Gtxn[1].xfer_asset() == asset_a,
             Gtxn[2].type_enum() == Int(4),
             Gtxn[2].xfer_asset() == asset_c,
             Gtxn[2].asset_amount() == redeem_round * supply * price_decrement,
             Gtxn[3].type_enum() == Int(1),
             Gtxn[3].amount() == Gtxn[1].fee() + Gtxn[2].fee(),
             Gtxn[1].asset_amount() ==
             Gtxn[0].asset_amount() * (start_price - price_decrement * Btoi(Arg(0))),
             Gtxn[0].sender() == Gtxn[1].receiver(),
             Gtxn[0].receiver() == Gtxn[1].sender(),
             Gtxn[1].sender() == Gtxn[2].sender(),
             Gtxn[2].sender() == Gtxn[2].receiver(),
             Gtxn[2].receiver() == Gtxn[3].receiver())
             
wrapup = And(Global.group_size() == Int(1),
             Txn.first_valid() >= start_round + wrapup_time,
             Or(And(Txn.type_enum() == Int(1),
                    Txn.amount() == Int(0),
                    Txn.close_remainder_to() == receiver),
                And(Txn.type_enum() == Int(4),
                    Txn.asset_amount() == Int(0),
                    Txn.asset_close_to() == receiver,
                    Txn.xfer_asset() == asset_a)))


dutch = Cond([Global.group_size() == Int(5), bid],
             [Global.group_size() == Int(4), redeem],
             [Global.group_size() == Int(1), wrapup])

print(compileTeal(dutch, Mode.Signature))
