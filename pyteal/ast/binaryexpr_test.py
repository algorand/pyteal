import pytest

from ..errors import TealTypeError
from . import *

def test_add():
    Int(2) + Int(3)

    with pytest.raises(TealTypeError):
        Int(2) + Txn.receiver()

def test_minus():
    Int(5) - Int(6)

    with pytest.raises(TealTypeError):
        Int(2) - Txn.receiver()

def test_mul():
    Int(3) * Int(8)

    with pytest.raises(TealTypeError):
        Int(2) * Txn.receiver()

def test_div():
    Int(9) / Int(3)

    with pytest.raises(TealTypeError):
        Int(2) / Txn.receiver()

def test_mod():
    Int(10) % Int(9)

    with pytest.raises(TealTypeError):
        Txn.receiver() % Int(2)

def test_arithmic():
    v = ((Int(2) + Int(3))/((Int(5) - Int(6)) * Int(8))) % Int(9)
    assert v.__teal__() == \
        [['int', '2'], ['int', '3'], ['+'], ['int', '5'], ['int', '6']] + \
        [['-'], ['int', '8'], ['*'], ['/'], ['int', '9'], ['%']]

    with pytest.raises(TealTypeError):
        Int(2) + Txn.receiver()

    with pytest.raises(TealTypeError):
        Int(2) - Txn.receiver()

    with pytest.raises(TealTypeError):
        Int(2) * Txn.receiver()

    with pytest.raises(TealTypeError):
        Int(2) / Txn.receiver()

    with pytest.raises(TealTypeError):
        Txn.receiver() % Int(2)

def test_eq():
    Eq(Int(2), Int(3))
    Eq(Txn.receiver(), Txn.sender())

    with pytest.raises(TealTypeError):
        Eq(Txn.fee(), Txn.receiver())

def test_lt():
    Lt(Int(2), Int(3))

    with pytest.raises(TealTypeError):
        Lt(Txn.fee(), Txn.receiver())

def test_le():
    Int(1) <= Int(2)

    with pytest.raises(TealTypeError):
        Int(1) <= Txn.receiver()

def test_gt():
    Gt(Int(2), Int(3))

    with pytest.raises(TealTypeError):
        Gt(Txn.fee(), Txn.receiver())

def test_ge():
    Int(1) >= Int(1)

    with pytest.raises(TealTypeError):
        Int(1) >= Txn.receiver()
