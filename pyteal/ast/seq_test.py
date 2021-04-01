import pytest

from .. import *
# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()

def test_seq_one():
    items = [Int(0)]
    expr = Seq(items)
    assert expr.type_of() == TealType.uint64

    expected, _ = items[0].__teal__(options)

    actual, _ = expr.__teal__(options)

    assert actual == expected

def test_seq_two():
    items = [
        App.localPut(Int(0), Bytes("key"), Int(1)),
        Int(7)
    ]
    expr = Seq(items)
    assert expr.type_of() == items[-1].type_of()

    expected, first_end = items[0].__teal__(options)
    first_end.setNextBlock(items[1].__teal__(options)[0])
    expected.addIncoming()
    expected = TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
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
    
    expected, first_end = items[0].__teal__(options)
    second_start, second_end = items[1].__teal__(options)
    first_end.setNextBlock(second_start)
    third_start, _ = items[2].__teal__(options)
    second_end.setNextBlock(third_start)

    expected.addIncoming()
    expected = TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(options)
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
