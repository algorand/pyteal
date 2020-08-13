import pytest

from .. import *

def test_cond_one_pred():
    teal = Cond([Int(1), Int(2)]).__teal__()
    assert len(teal) == 6
    labels = [teal[3][0], teal[5][0]]
    assert all(label.endswith(":") for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        ["int", "1"],
        ["bnz", labels[0][:-1]],
        ["err"],
        [labels[0]],
        ["int", "2"],
        [labels[1]]
    ]

def test_cond_two_pred():
    teal = Cond([Int(1), Int(2)], [Int(0), Int(3)]).__teal__()
    assert len(teal) == 12
    labels = [teal[5][0], teal[9][0], teal[11][0]]
    assert all(label.endswith(":") for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        ["int", "1"],
        ["bnz", labels[0][:-1]],
        ["int", "0"],
        ["bnz", labels[1][:-1]],
        ["err"],
        [labels[0]],
        ["int", "2"],
        ["int", "1"],
        ["bnz", labels[2][:-1]],
        [labels[1]],
        ["int", "3"],
        [labels[2]]
    ]

def test_cond_three_pred():
    teal = Cond([Int(1), Int(2)], [Int(3), Int(4)], [Int(5), Int(6)]).__teal__()
    assert len(teal) == 18
    labels = [teal[7][0], teal[11][0], teal[15][0], teal[17][0]]
    assert all(label.endswith(":") for label in labels)
    assert len(labels) == len(set(labels))
    assert teal == [
        ["int", "1"],
        ["bnz", labels[0][:-1]],
        ["int", "3"],
        ["bnz", labels[1][:-1]],
        ["int", "5"],
        ["bnz", labels[2][:-1]],
        ["err"],
        [labels[0]],
        ["int", "2"],
        ["int", "1"],
        ["bnz", labels[3][:-1]],
        [labels[1]],
        ["int", "4"],
        ["int", "1"],
        ["bnz", labels[3][:-1]],
        [labels[2]],
        ["int", "6"],
        [labels[3]]
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
