import pytest

from .. import *

def test_seq_one():
    expr = Seq([Int(0)])
    assert expr.type_of() == TealType.uint64

    expected, _ = Int(0).__teal__()

    actual, _ = expr.__teal__()

    assert actual == expected

def test_seq_two():
    items = [
        App.localPut(Int(0), Bytes("key"), Int(1)),
        Int(7)
    ]
    expr = Seq(items)
    assert expr.type_of() == items[-1].type_of()

    expected, first_end = items[0].__teal__()
    first_end.setNextBlock(items[1].__teal__()[0])
    expected.addIncoming()
    expected = TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__()
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_seq_three():
    items = [
        App.localPut(Int(0), Bytes("key1"), Int(1)),
        App.localPut(Int(1), Bytes("key2"), Bytes("value2")),
        Pop(Bytes("end"))
    ]
    expr = Seq(items)
    assert expr.type_of() == items[-1].type_of()
    
    expected, first_end = items[0].__teal__()
    second_start, second_end = items[1].__teal__()
    first_end.setNextBlock(second_start)
    third_start, _ = items[2].__teal__()
    second_end.setNextBlock(third_start)

    expected.addIncoming()
    expected = TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__()
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_seq_invalid():
    with pytest.raises(TealInputError):
        Seq([])
    
    with pytest.raises(TealTypeError):
        Seq([Int(1), Pop(Int(2))])
    
    with pytest.raises(TealTypeError):
        Seq([Int(1), Int(2)])
    
    with pytest.raises(TealTypeError):
        Seq([Seq([Pop(Int(1)), Int(2)]), Int(3)])
