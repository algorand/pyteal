import pyteal

from .global_ import Global

def test_global():
    Global.min_txn_fee()
    Global.min_balance()
    Global.max_txn_life()
    Global.zero_address()
    Global.group_size()
