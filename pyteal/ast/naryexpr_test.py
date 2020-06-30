import pytest

from .. import *

def test_and_two():
    expr = And(Int(1), Int(2))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 2),
        TealOp(Op.logic_and)
    ]

def test_and_three():
    expr = And(Int(1), Int(2), Int(3))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 2),
        TealOp(Op.logic_and),
        TealOp(Op.int, 3),
        TealOp(Op.logic_and)
    ]

def test_and_overload():
    expr = Int(1).And(Int(2))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 2),
        TealOp(Op.logic_and)
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
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 0),
        TealOp(Op.logic_or)
    ]

def test_or_three():
    expr = Or(Int(0), Int(1), Int(2))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.int, 1),
        TealOp(Op.logic_or),
        TealOp(Op.int, 2),
        TealOp(Op.logic_or)
    ]

def test_or_overload():
    expr = Int(1).Or(Int(0))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 0),
        TealOp(Op.logic_or)
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
