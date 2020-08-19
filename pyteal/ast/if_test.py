import pytest

from .. import *

def test_if_int():
    expr = If(Int(0), Int(1), Int(2))
    assert expr.type_of() == TealType.uint64
    teal = expr.__teal__()
    assert len(teal) == 7
    labels = [teal[4], teal[6]]
    assert all(isinstance(label, TealLabel) for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        TealOp(Op.int, 0),
        TealOp(Op.bnz, labels[0].label),
        TealOp(Op.int, 2),
        TealOp(Op.b, labels[1].label),
        labels[0],
        TealOp(Op.int, 1),
        labels[1]
    ]

def test_if_bytes():
    expr = If(Int(0), Txn.sender(), Txn.receiver())
    assert expr.type_of() == TealType.bytes
    teal = expr.__teal__()
    assert len(teal) == 7
    labels = [teal[4], teal[6]]
    assert all(isinstance(label, TealLabel) for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        TealOp(Op.int, 0),
        TealOp(Op.bnz, labels[0].label),
        TealOp(Op.txn, "Receiver"),
        TealOp(Op.b, labels[1].label),
        labels[0],
        TealOp(Op.txn, "Sender"),
        labels[1]
    ]

def test_if_none():
    expr = If(Int(0), Pop(Txn.sender()), Pop(Txn.receiver()))
    assert expr.type_of() == TealType.none
    teal = expr.__teal__()
    assert len(teal) == 9
    labels = [teal[5], teal[8]]
    assert all(isinstance(label, TealLabel) for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        TealOp(Op.int, 0),
        TealOp(Op.bnz, labels[0].label),
        TealOp(Op.txn, "Receiver"),
        TealOp(Op.pop),
        TealOp(Op.b, labels[1].label),
        labels[0],
        TealOp(Op.txn, "Sender"),
        TealOp(Op.pop),
        labels[1]
    ]

def test_if_single():
    expr = If(Int(0), Pop(Int(1)))
    assert expr.type_of() == TealType.none
    teal = expr.__teal__()
    assert len(teal) == 5
    labels = [teal[4]]
    assert all(isinstance(label, TealLabel) for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        TealOp(Op.int, 0),
        TealOp(Op.bz, labels[0].label),
        TealOp(Op.int, 1),
        TealOp(Op.pop),
        labels[0]
    ]

def test_if_invalid():
    with pytest.raises(TealTypeError):
        If(Int(0), Txn.amount(), Txn.sender())

    with pytest.raises(TealTypeError):
        If(Txn.sender(), Int(1), Int(0))
    
    with pytest.raises(TealTypeError):
        If(Int(0), Int(1))
    
    with pytest.raises(TealTypeError):
        If(Int(0), Txn.sender())
