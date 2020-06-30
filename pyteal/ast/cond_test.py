import pytest

from .. import *

def test_cond_one_pred():
    expr = Cond([Int(1), Int(2)])
    assert expr.type_of() == TealType.uint64
    teal = expr.__teal__()
    assert len(teal) == 6
    labels = [teal[3], teal[5]]
    assert all(isinstance(label, TealLabel) for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        TealOp(Op.int, 1),
        TealOp(Op.bnz, labels[0].label),
        TealOp(Op.err),
        labels[0],
        TealOp(Op.int, 2),
        labels[1]
    ]

def test_cond_two_pred():
    expr = Cond([Int(1), Bytes("one")], [Int(0), Bytes("zero")])
    assert expr.type_of() == TealType.bytes
    teal = expr.__teal__()
    assert len(teal) == 11
    labels = [teal[5], teal[8], teal[10]]
    assert all(isinstance(label, TealLabel) for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        TealOp(Op.int, 1),
        TealOp(Op.bnz, labels[0].label),
        TealOp(Op.int, 0),
        TealOp(Op.bnz, labels[1].label),
        TealOp(Op.err),
        labels[0],
        TealOp(Op.byte, "\"one\""),
        TealOp(Op.b, labels[2].label),
        labels[1],
        TealOp(Op.byte, "\"zero\""),
        labels[2]
    ]

def test_cond_three_pred():
    expr = Cond([Int(1), Int(2)], [Int(3), Int(4)], [Int(5), Int(6)])
    assert expr.type_of() == TealType.uint64
    teal = expr.__teal__()
    assert len(teal) == 16
    labels = [teal[7], teal[10], teal[13], teal[15]]
    assert all(isinstance(label, TealLabel) for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        TealOp(Op.int, 1),
        TealOp(Op.bnz, labels[0].label),
        TealOp(Op.int, 3),
        TealOp(Op.bnz, labels[1].label),
        TealOp(Op.int, 5),
        TealOp(Op.bnz, labels[2].label),
        TealOp(Op.err),
        labels[0],
        TealOp(Op.int, 2),
        TealOp(Op.b, labels[3].label),
        labels[1],
        TealOp(Op.int, 4),
        TealOp(Op.b, labels[3].label),
        labels[2],
        TealOp(Op.int, 6),
        labels[3]
    ]

def test_cond_invalid():
    with pytest.raises(TealInputError):
        Cond()

    with pytest.raises(TealInputError):
        Cond([])

    with pytest.raises(TealTypeError):
        Cond([Int(1), Int(2)], [Int(2), Txn.receiver()])

    with pytest.raises(TealTypeError):
        Cond([Arg(0), Int(2)])
