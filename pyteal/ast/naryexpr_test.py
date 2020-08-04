import pytest

from .. import *

def test_and_two():
    expr = And(Int(1), Int(2))
    assert expr.__teal__() == [
        ["int", "1"],
        ["int", "2"],
        ["&&"]
    ]

def test_and_three():
    expr = And(Int(1), Int(2), Int(3))
    assert expr.__teal__() == [
        ["int", "1"],
        ["int", "2"],
        ["&&"],
        ["int", "3"],
        ["&&"]
    ]

def test_and_overload():
    expr = Int(1).And(Int(2))
    assert expr.__teal__() == [
        ["int", "1"],
        ["int", "2"],
        ["&&"]
    ]

def test_and_invalid():
    with pytest.raises(TealInputError):
        And()
    
    with pytest.raises(TealInputError):
        And(Int(1))

    with pytest.raises(TealTypeError):
        And(Int(1), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        And(Txn.receiver(), Int(1))
    
    with pytest.raises(TealTypeError):
        And(Txn.receiver(), Txn.receiver())

def test_or_two():
    expr = Or(Int(1), Int(0))
    assert expr.__teal__() == [
        ["int", "1"],
        ["int", "0"],
        ["||"]
    ]

def test_or_three():
    expr = Or(Int(0), Int(1), Int(2))
    assert expr.__teal__() == [
        ["int", "0"],
        ["int", "1"],
        ["||"],
        ["int", "2"],
        ["||"]
    ]

def test_or_overload():
    expr = Int(1).Or(Int(0))
    assert expr.__teal__() == [
        ["int", "1"],
        ["int", "0"],
        ["||"]
    ]

def test_or_invalid():
    with pytest.raises(TealInputError):
        Or()

    with pytest.raises(TealInputError):
        Or(Int(1))

    with pytest.raises(TealTypeError):
        Or(Int(1), Txn.receiver())

    with pytest.raises(TealTypeError):
        Or(Txn.receiver(), Int(1))
    
    with pytest.raises(TealTypeError):
        Or(Txn.receiver(), Txn.receiver())
