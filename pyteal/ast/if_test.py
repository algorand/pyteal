import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_if_has_return():
    exprWithReturn = If(Int(1), Return(Int(1)), Return(Int(0)))
    assert exprWithReturn.has_return()

    exprWithoutReturn = If(Int(1), Int(1), Int(0))
    assert not exprWithoutReturn.has_return()

    exprSemiReturn = If(
        Int(1), Return(Int(1)), App.globalPut(Bytes("key"), Bytes("value"))
    )
    assert not exprSemiReturn.has_return()


def test_if_int():
    args = [Int(0), Int(1), Int(2)]
    expr = If(args[0], args[1], args[2])
    assert expr.type_of() == TealType.uint64

    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseBlock, _ = args[2].__teal__(options)
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseBlock)
    expected.setNextBlock(expectedBranch)
    end = TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseBlock.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_bytes():
    args = [Int(1), Txn.sender(), Txn.receiver()]
    expr = If(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseBlock, _ = args[2].__teal__(options)
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseBlock)
    expected.setNextBlock(expectedBranch)
    end = TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseBlock.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_none():
    args = [Int(0), Pop(Txn.sender()), Pop(Txn.receiver())]
    expr = If(args[0], args[1], args[2])
    assert expr.type_of() == TealType.none

    expected, _ = args[0].__teal__(options)
    thenBlockStart, thenBlockEnd = args[1].__teal__(options)
    elseBlockStart, elseBlockEnd = args[2].__teal__(options)
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlockStart)
    expectedBranch.setFalseBlock(elseBlockStart)
    expected.setNextBlock(expectedBranch)
    end = TealSimpleBlock([])
    thenBlockEnd.setNextBlock(end)
    elseBlockEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_single():
    args = [Int(1), Pop(Int(1))]
    expr = If(args[0], args[1])
    assert expr.type_of() == TealType.none

    expected, _ = args[0].__teal__(options)
    thenBlockStart, thenBlockEnd = args[1].__teal__(options)
    end = TealSimpleBlock([])
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlockStart)
    expectedBranch.setFalseBlock(end)
    expected.setNextBlock(expectedBranch)
    thenBlockEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_invalid():
    with pytest.raises(TealTypeError):
        If(Int(0), Txn.amount(), Txn.sender())

    with pytest.raises(TealTypeError):
        If(Txn.sender(), Int(1), Int(0))

    with pytest.raises(TealTypeError):
        If(Int(0), Txn.sender())

    with pytest.raises(TealTypeError):
        If(Int(0), Int(2))

    with pytest.raises(TealCompileError):
        expr = If(Int(0))
        expr.__teal__(options)


def test_if_alt_int():
    args = [Int(0), Int(1), Int(2)]
    expr = If(args[0]).Then(args[1]).Else(args[2])
    assert expr.type_of() == TealType.uint64

    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseBlock, _ = args[2].__teal__(options)
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseBlock)
    expected.setNextBlock(expectedBranch)
    end = TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseBlock.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_alt_bytes():
    args = [Int(1), Txn.sender(), Txn.receiver()]
    expr = If(args[0]).Then(args[1]).Else(args[2])
    assert expr.type_of() == TealType.bytes

    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseBlock, _ = args[2].__teal__(options)
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseBlock)
    expected.setNextBlock(expectedBranch)
    end = TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseBlock.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_alt_none():
    args = [Int(0), Pop(Txn.sender()), Pop(Txn.receiver())]
    expr = If(args[0]).Then(args[1]).Else(args[2])
    assert expr.type_of() == TealType.none

    expected, _ = args[0].__teal__(options)
    thenBlockStart, thenBlockEnd = args[1].__teal__(options)
    elseBlockStart, elseBlockEnd = args[2].__teal__(options)
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlockStart)
    expectedBranch.setFalseBlock(elseBlockStart)
    expected.setNextBlock(expectedBranch)
    end = TealSimpleBlock([])
    thenBlockEnd.setNextBlock(end)
    elseBlockEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_elseif_syntax():
    args = [Int(0), Int(1), Int(2), Int(3), Int(4)]
    expr = If(args[0]).Then(args[1]).ElseIf(args[2]).Then(args[3]).Else(args[4])
    assert expr.type_of() == TealType.uint64

    elseExpr = If(args[2]).Then(args[3]).Else(args[4])
    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseStart, elseEnd = elseExpr.__teal__(options)
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseStart)
    expected.setNextBlock(expectedBranch)
    end = TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_elseif_multiple():
    args = [Int(0), Int(1), Int(2), Int(3), Int(4), Int(5), Int(6)]
    expr = (
        If(args[0])
        .Then(args[1])
        .ElseIf(args[2])
        .Then(args[3])
        .ElseIf(args[4])
        .Then(args[5])
        .Else(args[6])
    )
    assert expr.type_of() == TealType.uint64

    elseIfExpr = If(args[2], args[3], If(args[4], args[5], args[6]))
    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseStart, elseEnd = elseIfExpr.__teal__(options)
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseStart)
    expected.setNextBlock(expectedBranch)
    end = TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_invalid_alt_syntax():
    with pytest.raises(TealCompileError):
        expr = If(Int(0)).ElseIf(Int(1))
        expr.__teal__(options)

    with pytest.raises(TealCompileError):
        expr = If(Int(0)).ElseIf(Int(1)).Then(Int(2))
        expr.__teal__(options)

    with pytest.raises(TealCompileError):
        expr = If(Int(0)).Then(Int(1)).ElseIf(Int(2))
        expr.__teal__(options)

    with pytest.raises(TealCompileError):
        expr = If(Int(0)).Then(Int(1)).ElseIf(Int(2))
        expr.__teal__(options)

    with pytest.raises(TealCompileError):
        expr = If(Int(0)).Else(Int(1))
        expr.__teal__(options)

    with pytest.raises(TealInputError):
        expr = If(Int(0)).Else(Int(1)).Then(Int(2))

    with pytest.raises(TealInputError):
        expr = If(Int(0)).Else(Int(1)).Else(Int(2))

    with pytest.raises(TealInputError):
        expr = If(Int(0), Pop(Int(1))).Else(Int(2))
