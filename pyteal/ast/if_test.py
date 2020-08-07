import pytest

from .. import *

def test_if_int():
    expr = If(Int(0), Int(1), Int(2))
    assert expr.type_of() == TealType.uint64

    expected, _ = Int(0).__teal__()
    expected.setTrueBlock(Int(1).__teal__()[0])
    expected.setFalseBlock(Int(2).__teal__()[0])

    actual, _ = expr.__teal__()
    actual.trim()

    assert actual == expected

def test_if_bytes():
    expr = If(Int(1), Txn.sender(), Txn.receiver())
    assert expr.type_of() == TealType.bytes

    expected, _ = Int(1).__teal__()
    expected.setTrueBlock(Txn.sender().__teal__()[0])
    expected.setFalseBlock(Txn.receiver().__teal__()[0])

    actual, _ = expr.__teal__()
    actual.trim()

    assert actual == expected

def test_if_none():
    expr = If(Int(0), Pop(Txn.sender()), Pop(Txn.receiver()))
    assert expr.type_of() == TealType.none

    expected, _ = Int(0).__teal__()
    expected.setTrueBlock(Pop(Txn.sender()).__teal__()[0])
    expected.setFalseBlock(Pop(Txn.receiver()).__teal__()[0])

    actual, _ = expr.__teal__()
    actual.trim()

    assert actual == expected

def test_if_single():
    expr = If(Int(1), Pop(Int(1)))
    assert expr.type_of() == TealType.none

    expected, _ = Int(1).__teal__()
    expected.setTrueBlock(Pop(Int(1)).__teal__()[0])

    actual, _ = expr.__teal__()
    actual.trim()
    
    assert actual == expected

def test_if_invalid():
    with pytest.raises(TealTypeError):
        If(Int(0), Txn.amount(), Txn.sender())

    with pytest.raises(TealTypeError):
        If(Txn.sender(), Int(1), Int(0))
    
    with pytest.raises(TealTypeError):
        If(Int(0), Int(1))
    
    with pytest.raises(TealTypeError):
        If(Int(0), Txn.sender())
