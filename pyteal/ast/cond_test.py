import pytest

from .. import *

def test_cond_one_pred():
    expr = Cond([Int(1), Int(2)])
    assert expr.type_of() == TealType.uint64

    expected, _ = Int(1).__teal__()
    expected.setTrueBlock(Int(2).__teal__()[0])
    expected.setFalseBlock(Err().__teal__()[0])

    actual, _ = expr.__teal__()
    actual.trim()

    assert actual == expected

def test_cond_two_pred():
    expr = Cond([Int(1), Bytes("one")], [Int(0), Bytes("zero")])
    assert expr.type_of() == TealType.bytes

    expected, _ = Int(1).__teal__()
    expected.setTrueBlock(Bytes("one").__teal__()[0])

    first_false, _ = Int(0).__teal__()
    first_false.setTrueBlock(Bytes("zero").__teal__()[0])
    first_false.setFalseBlock(Err().__teal__()[0])
    expected.setFalseBlock(first_false)

    actual, _ = expr.__teal__()
    actual.trim()

    assert actual == expected

def test_cond_three_pred():
    expr = Cond([Int(1), Int(2)], [Int(3), Int(4)], [Int(5), Int(6)])
    assert expr.type_of() == TealType.uint64

    expected, _ = Int(1).__teal__()
    expected.setTrueBlock(Int(2).__teal__()[0])
    first_false, _ = Int(3).__teal__()
    first_false.setTrueBlock(Int(4).__teal__()[0])
    second_false, _ = Int(5).__teal__()
    second_false.setTrueBlock(Int(6).__teal__()[0])
    second_false.setFalseBlock(Err().__teal__()[0])
    first_false.setFalseBlock(second_false)
    expected.setFalseBlock(first_false)

    actual, _ = expr.__teal__()
    actual.trim()

    assert actual == expected

def test_cond_invalid():
    with pytest.raises(TealInputError):
        Cond()

    with pytest.raises(TealInputError):
        Cond([])

    with pytest.raises(TealTypeError):
        Cond([Int(1), Int(2)], [Int(2), Txn.receiver()])

    with pytest.raises(TealTypeError):
        Cond([Arg(0), Int(2)])
