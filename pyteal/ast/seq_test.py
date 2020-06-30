import pytest

from .. import *

def test_seq_one():
    items = [Int(0)]
    expr = Seq(items)
    assert expr.type_of() == items[-1].type_of()
    assert expr.__teal__() == [op for item in items for op in item.__teal__()]

def test_seq_two():
    items = [
        App.localPut(Int(0), Bytes("key"), Int(1)),
        Int(7)
    ]
    expr = Seq(items)
    assert expr.type_of() == items[-1].type_of()
    assert expr.__teal__() == [op for item in items for op in item.__teal__()]

def test_seq_three():
    items = [
        App.localPut(Int(0), Bytes("key1"), Int(1)),
        App.localPut(Int(1), Bytes("key2"), Bytes("value2")),
        Pop(Bytes("end"))
    ]
    expr = Seq(items)
    assert expr.type_of() == items[-1].type_of()
    assert expr.__teal__() == [op for item in items for op in item.__teal__()]


def test_seq_invalid():
    with pytest.raises(TealInputError):
        Seq([])
    
    with pytest.raises(TealTypeError):
        Seq([Int(1), Pop(Int(2))])
    
    with pytest.raises(TealTypeError):
        Seq([Int(1), Int(2)])
    
    with pytest.raises(TealTypeError):
        Seq([Seq([Pop(Int(1)), Int(2)]), Int(3)])
