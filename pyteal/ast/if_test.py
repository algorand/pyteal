import pytest

from .. import *

def test_if_int():
    expr = If(Int(0), Int(1), Int(2))
    assert expr.type_of() == TealType.uint64

    expected, _ = Int(0).__teal__()
    thenBlock, _ = Int(1).__teal__()
    elseBlock, _ = Int(2).__teal__()
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseBlock)
    expected.setNextBlock(expectedBranch)
    end = TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseBlock.setNextBlock(end)

    actual, _ = expr.__teal__()

    assert actual == expected

def test_if_bytes():
    expr = If(Int(1), Txn.sender(), Txn.receiver())
    assert expr.type_of() == TealType.bytes

    expected, _ = Int(1).__teal__()
    thenBlock, _ = Txn.sender().__teal__()
    elseBlock, _ = Txn.receiver().__teal__()
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseBlock)
    expected.setNextBlock(expectedBranch)
    end = TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseBlock.setNextBlock(end)

    actual, _ = expr.__teal__()

    assert actual == expected

def test_if_none():
    expr = If(Int(0), Pop(Txn.sender()), Pop(Txn.receiver()))
    assert expr.type_of() == TealType.none

    expected, _ = Int(0).__teal__()
    thenBlockStart, thenBlockEnd = Pop(Txn.sender()).__teal__()
    elseBlockStart, elseBlockEnd = Pop(Txn.receiver()).__teal__()
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlockStart)
    expectedBranch.setFalseBlock(elseBlockStart)
    expected.setNextBlock(expectedBranch)
    end = TealSimpleBlock([])
    thenBlockEnd.setNextBlock(end)
    elseBlockEnd.setNextBlock(end)

    actual, _ = expr.__teal__()

    assert actual == expected

def test_if_single():
    expr = If(Int(1), Pop(Int(1)))
    assert expr.type_of() == TealType.none

    expected, _ = Int(1).__teal__()
    thenBlockStart, thenBlockEnd = Pop(Int(1)).__teal__()
    end = TealSimpleBlock([])
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlockStart)
    expectedBranch.setFalseBlock(end)
    expected.setNextBlock(expectedBranch)
    thenBlockEnd.setNextBlock(end)

    actual, _ = expr.__teal__()
    
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
