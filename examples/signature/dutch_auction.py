# This example is provided for informational purposes only and has not been audited for security.

from pyteal import *


""" Template for layer 1 dutch auction (from Fabrice and Shai)
"""

tmpl_start_round = Tmpl.Int("TMPL_START_ROUND")
tmpl_start_price = Tmpl.Int("TMPL_START_PRICE")
tmpl_supply = Tmpl.Int("TMPL_N")
tmpl_price_decrement = Tmpl.Int("TMPL_PRICE_INCREMENT")
tmpl_period = Tmpl.Int("TMPL_PERIOD")
tmpl_asset_a = Tmpl.Int("TMPL_ASSET_A")
tmpl_asset_b = Tmpl.Int("TMPL_ASSET_B")
tmpl_asset_c = Tmpl.Int("TMPL_ASSET_C")
tmpl_asset_d = Tmpl.Int("TMPL_ASSET_D")
tmpl_receiver = Tmpl.Addr("TMPL_RECEIVER")
tmpl_algo_sink = Tmpl.Addr("TMPL_ALGO_ZERO")
tmpl_asset_a_sink = Tmpl.Addr("TMPL_A_ZERO")
tmpl_asset_b_sink = Tmpl.Addr("TMPL_B_ZERO")
tmpl_asset_c_sink = Tmpl.Addr("TMPL_C_ZERO")
tmpl_asset_d_sink = Tmpl.Addr("TMPL_D_ZERO")
tmpl_redeem_round = Tmpl.Int("TMPL_REDEEM_ROUND")
tmpl_wrapup_time = Tmpl.Int("TMPL_WRAPUP_ROUND")


def dutch_auction(
    start_round=tmpl_start_round,
    start_price=tmpl_start_price,
    supply=tmpl_supply,
    price_decrement=tmpl_price_decrement,
    period=tmpl_period,
    asset_a=tmpl_asset_a,
    asset_b=tmpl_asset_b,
    asset_c=tmpl_asset_c,
    asset_d=tmpl_asset_d,
    receiver=tmpl_receiver,
    algo_sink=tmpl_algo_sink,
    asset_a_sink=tmpl_asset_a_sink,
    asset_b_sink=tmpl_asset_b_sink,
    asset_c_sink=tmpl_asset_c_sink,
    asset_d_sink=tmpl_asset_d_sink,
    redeem_round=tmpl_redeem_round,
    wrapup_time=tmpl_wrapup_time,
):
    # the definition of i simplifies the original desgin by only constraining last_valid here
    i_upper = (Gtxn[0].last_valid() - start_round) / period

    bid = And(
        Gtxn[0].rekey_to() == Global.zero_address(),
        Gtxn[1].rekey_to() == Global.zero_address(),
        Gtxn[2].rekey_to() == Global.zero_address(),
        Gtxn[3].rekey_to() == Global.zero_address(),
        Gtxn[4].rekey_to() == Global.zero_address(),
        Gtxn[0].last_valid() == Gtxn[1].last_valid(),
        Gtxn[1].last_valid() == Gtxn[2].last_valid(),
        Gtxn[2].last_valid() == Gtxn[3].last_valid(),
        Gtxn[3].last_valid() == Gtxn[4].last_valid(),
        Gtxn[4].last_valid() < (start_round + i_upper * period),
        Gtxn[0].type_enum() == TxnType.AssetTransfer,
        Gtxn[0].xfer_asset() == asset_d,
        Gtxn[0].receiver() == receiver,
        Gtxn[1].type_enum() == TxnType.AssetTransfer,
        Gtxn[1].xfer_asset() == asset_b,
        Gtxn[2].type_enum() == TxnType.AssetTransfer,
        Gtxn[2].xfer_asset() == asset_c,
        Gtxn[3].type_enum() == TxnType.AssetTransfer,
        Gtxn[4].xfer_asset() == asset_c,
        Gtxn[4].type_enum() == TxnType.Payment,
        Gtxn[4].amount()
        == (Gtxn[1].fee() + Gtxn[2].fee() + Gtxn[3].fee()),  # ? why only 1, 2, 3
        Gtxn[0].asset_amount() == Gtxn[1].asset_amount(),
        Gtxn[1].asset_amount() == Gtxn[2].asset_amount(),
        Gtxn[3].asset_amount() == i_upper * supply * price_decrement,
        Gtxn[0].sender() == Gtxn[1].receiver(),
        Gtxn[2].receiver() == asset_c_sink,
        Gtxn[1].sender() == Gtxn[2].sender(),
        Gtxn[2].sender() == Gtxn[3].sender(),
        Gtxn[3].sender() == Gtxn[3].receiver(),
        Gtxn[3].receiver() == Gtxn[4].receiver(),
    )

    redeem = And(
        Gtxn[0].rekey_to() == Global.zero_address(),
        Gtxn[1].rekey_to() == Global.zero_address(),
        Gtxn[2].rekey_to() == Global.zero_address(),
        Gtxn[3].rekey_to() == Global.zero_address(),
        Gtxn[0].first_valid() == Gtxn[1].first_valid(),
        Gtxn[1].first_valid() == Gtxn[2].first_valid(),
        Gtxn[2].first_valid() == Gtxn[3].first_valid(),
        Gtxn[3].first_valid() >= redeem_round,
        Gtxn[0].type_enum() == TxnType.AssetTransfer,
        Gtxn[0].xfer_asset() == asset_b,
        Gtxn[1].type_enum() == TxnType.AssetTransfer,
        Gtxn[1].xfer_asset() == asset_a,
        Gtxn[2].type_enum() == TxnType.AssetTransfer,
        Gtxn[2].xfer_asset() == asset_c,
        Gtxn[2].asset_amount() == redeem_round * supply * price_decrement,
        Gtxn[3].type_enum() == TxnType.Payment,
        Gtxn[3].amount() == Gtxn[1].fee() + Gtxn[2].fee(),
        Gtxn[1].asset_amount()
        == Gtxn[0].asset_amount() * (start_price - price_decrement * Btoi(Arg(0))),
        Gtxn[0].sender() == Gtxn[1].receiver(),
        Gtxn[0].receiver() == Gtxn[1].sender(),
        Gtxn[1].sender() == Gtxn[2].sender(),
        Gtxn[2].sender() == Gtxn[2].receiver(),
        Gtxn[2].receiver() == Gtxn[3].receiver(),
    )

    wrapup = And(
        Txn.rekey_to() == Global.zero_address(),
        Txn.first_valid() >= start_round + wrapup_time,
        Or(
            And(
                Txn.type_enum() == TxnType.Payment,
                Txn.amount() == Int(0),
                Txn.close_remainder_to() == receiver,
            ),
            And(
                Txn.type_enum() == TxnType.AssetTransfer,
                Txn.asset_amount() == Int(0),
                Txn.asset_close_to() == receiver,
                Txn.xfer_asset() == asset_a,
            ),
        ),
    )

    dutch = Cond(
        [Global.group_size() == Int(5), bid],
        [Global.group_size() == Int(4), redeem],
        [Global.group_size() == Int(1), wrapup],
    )

    return dutch


if __name__ == "__main__":
    print(compileTeal(dutch_auction(), mode=Mode.Signature, version=2))
