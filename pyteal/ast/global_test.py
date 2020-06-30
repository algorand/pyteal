import pyteal

from .. import *

def test_global_min_txn_fee():
    expr = Global.min_txn_fee()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.global_, "MinTxnFee")
    ]

def test_global_min_balance():
    expr = Global.min_balance()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.global_, "MinBalance")
    ]

def test_global_max_txn_life():
    expr = Global.max_txn_life()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.global_, "MaxTxnLife")
    ]

def test_global_zero_address():
    expr = Global.zero_address()
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.global_, "ZeroAddress")
    ]

def test_global_group_size():
    expr = Global.group_size()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.global_, "GroupSize")
    ]

def test_global_logic_sig_version():
    expr = Global.logic_sig_version()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.global_, "LogicSigVersion")
    ]

def test_global_round():
    expr = Global.round()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.global_, "Round")
    ]

def test_global_latest_timestamp():
    expr = Global.latest_timestamp()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.global_, "LatestTimestamp")
    ]

def test_global_current_application_id():
    expr = Global.current_application_id()
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.global_, "CurrentApplicationID")
    ]
