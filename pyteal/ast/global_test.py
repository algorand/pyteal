import pyteal

from .. import *

def test_global_min_txn_fee():
    expr = Global.min_txn_fee()
    assert expr.__teal__() == [
        ["global", "MinTxnFee"]
    ]

def test_global_min_balance():
    expr = Global.min_balance()
    assert expr.__teal__() == [
        ["global", "MinBalance"]
    ]

def test_global_max_txn_life():
    expr = Global.max_txn_life()
    assert expr.__teal__() == [
        ["global", "MaxTxnLife"]
    ]

def test_global_zero_address():
    expr = Global.zero_address()
    assert expr.__teal__() == [
        ["global", "ZeroAddress"]
    ]

def test_global_group_size():
    expr = Global.group_size()
    assert expr.__teal__() == [
        ["global", "GroupSize"]
    ]
