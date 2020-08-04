import pytest

from .. import *

def test_if_int():
    teal = If(Int(0), Int(1), Int(2)).__teal__()
    assert len(teal) == 9
    labels = [teal[6][0], teal[8][0]]
    assert all(label.endswith(":") for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        ["int", "0"],
        ["bnz", labels[0][:-1]],
        ["int", "2"],
        ["int", "1"],
        ["bnz", labels[1][:-1]],
        ["pop"],
        [labels[0]],
        ["int", "1"],
        [labels[1]]
    ]

def test_if_bytes():
    teal = If(Int(0), Txn.sender(), Txn.receiver()).__teal__()
    assert len(teal) == 9
    labels = [teal[6][0], teal[8][0]]
    assert all(label.endswith(":") for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        ["int", "0"],
        ["bnz", labels[0][:-1]],
        ["txn", "Receiver"],
        ["int", "1"],
        ["bnz", labels[1][:-1]],
        ["pop"],
        [labels[0]],
        ["txn", "Sender"],
        [labels[1]]
    ]

def test_if_invalid():
    with pytest.raises(TealTypeError):
        If(Int(0), Txn.amount(), Txn.sender())

    with pytest.raises(TealTypeError):
        If(Txn.sender(), Int(1), Int(0))
