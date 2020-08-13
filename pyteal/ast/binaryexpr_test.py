import pytest

from .. import *

def test_add():
    expr = Add(Int(2), Int(3))
    assert expr.__teal__() == [
        ["int", "2"],
        ["int", "3"],
        ["+"]
    ]

def test_add_overload():
    expr = Int(2) + Int(3) + Int(4)
    assert expr.__teal__() == [
        ["int", "2"],
        ["int", "3"],
        ["+"],
        ["int", "4"],
        ["+"]
    ]

def test_add_invalid():
    with pytest.raises(TealTypeError):
        Add(Int(2), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Add(Txn.sender(), Int(2))

def test_minus():
    expr = Minus(Int(5), Int(6))
    assert expr.__teal__() == [
        ["int", "5"],
        ["int", "6"],
        ["-"]
    ]

def test_minus_overload():
    expr = Int(10) - Int(1) - Int(2)
    assert expr.__teal__() == [
        ["int", "10"],
        ["int", "1"],
        ["-"],
        ["int", "2"],
        ["-"]
    ]

def test_minus_invalid():
    with pytest.raises(TealTypeError):
        Minus(Int(2), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Minus(Txn.sender(), Int(2))

def test_mul():
    expr = Mul(Int(3), Int(8))
    assert expr.__teal__() == [
        ["int", "3"],
        ["int", "8"],
        ["*"]
    ]

def test_mul_overload():
    expr = Int(3) * Int(8) * Int(10)
    assert expr.__teal__() == [
        ["int", "3"],
        ["int", "8"],
        ["*"],
        ["int", "10"],
        ["*"]
    ]

def test_mul_invalid():
    with pytest.raises(TealTypeError):
        Mul(Int(2), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Mul(Txn.sender(), Int(2))

def test_div():
    expr = Div(Int(9), Int(3))
    assert expr.__teal__() == [
        ["int", "9"],
        ["int", "3"],
        ["/"]
    ]

def test_div_overload():
    expr = Int(9) / Int(3) / Int(3)
    assert expr.__teal__() == [
        ["int", "9"],
        ["int", "3"],
        ["/"],
        ["int", "3"],
        ["/"],
    ]

def test_div_invalid():
    with pytest.raises(TealTypeError):
        Div(Int(2), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Div(Txn.sender(), Int(2))

def test_mod():
    expr = Mod(Int(10), Int(9))
    assert expr.__teal__() == [
        ["int", "10"],
        ["int", "9"],
        ["%"]
    ]

def test_mod_overload():
    expr = Int(10) % Int(9) % Int(100)
    assert expr.__teal__() == [
        ["int", "10"],
        ["int", "9"],
        ["%"],
        ["int", "100"],
        ["%"]
    ]

def test_mod_invalid():
    with pytest.raises(TealTypeError):
        Mod(Txn.receiver(), Int(2))
    
    with pytest.raises(TealTypeError):
        Mod(Int(2), Txn.sender())

def test_arithmetic():
    v = ((Int(2) + Int(3))/((Int(5) - Int(6)) * Int(8))) % Int(9)
    assert v.__teal__() == \
        [['int', '2'], ['int', '3'], ['+'], ['int', '5'], ['int', '6']] + \
        [['-'], ['int', '8'], ['*'], ['/'], ['int', '9'], ['%']]

def test_eq():
    expr_int = Eq(Int(2), Int(3))
    assert expr_int.__teal__() == [
        ["int", "2"],
        ["int", "3"],
        ["=="]
    ]

    expr_bytes = Eq(Txn.receiver(), Txn.sender())
    assert expr_bytes.__teal__() == [
        ["txn", "Receiver"],
        ["txn", "Sender"],
        ["=="]
    ]

def test_eq_overload():
    expr_int = Int(2) == Int(3)
    assert expr_int.__teal__() == [
        ["int", "2"],
        ["int", "3"],
        ["=="]
    ]

    expr_bytes = Txn.receiver() == Txn.sender()
    assert expr_bytes.__teal__() == [
        ["txn", "Receiver"],
        ["txn", "Sender"],
        ["=="]
    ]

def test_eq_invalid():
    with pytest.raises(TealTypeError):
        Eq(Txn.fee(), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Eq(Txn.sender(), Int(7))

def test_lt():
    expr = Lt(Int(2), Int(3))
    assert expr.__teal__() == [
        ["int", "2"],
        ["int", "3"],
        ["<"]
    ]

def test_lt_overload():
    expr = Int(2) < Int(3)
    assert expr.__teal__() == [
        ["int", "2"],
        ["int", "3"],
        ["<"]
    ]

def test_lt_invalid():
    with pytest.raises(TealTypeError):
        Lt(Int(7), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Lt(Txn.sender(), Int(7))

def test_le():
    expr = Le(Int(1), Int(2))
    assert expr.__teal__() == [
        ["int", "1"],
        ["int", "2"],
        ["<="]
    ]

def test_le_overload():
    expr = Int(1) <= Int(2)
    assert expr.__teal__() == [
        ["int", "1"],
        ["int", "2"],
        ["<="]
    ]

def test_le_invalid():
    with pytest.raises(TealTypeError):
        Le(Int(1), Txn.receiver())

    with pytest.raises(TealTypeError):
        Le(Txn.sender(), Int(1))

def test_gt():
    expr = Gt(Int(2), Int(3))
    assert expr.__teal__() == [
        ["int", "2"],
        ["int", "3"],
        [">"]
    ]

def test_gt_overload():
    expr = Int(2) > Int(3)
    assert expr.__teal__() == [
        ["int", "2"],
        ["int", "3"],
        [">"]
    ]

def test_gt_invalid():
    with pytest.raises(TealTypeError):
        Gt(Int(1), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Gt(Txn.receiver(), Int(1))

def test_ge():
    expr = Ge(Int(1), Int(10))
    assert expr.__teal__() == [
        ["int", "1"],
        ["int", "10"],
        [">="]
    ]

def test_ge_overload():
    expr = Int(1) >= Int(10)
    assert expr.__teal__() == [
        ["int", "1"],
        ["int", "10"],
        [">="]
    ]

def test_ge_invalid():
    with pytest.raises(TealTypeError):
        Ge(Int(1), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Ge(Txn.receiver(), Int(1))
