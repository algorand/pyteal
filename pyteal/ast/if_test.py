import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_if_has_return():
    exprWithReturn = pt.If(pt.Int(1), pt.Return(pt.Int(1)), pt.Return(pt.Int(0)))
    assert exprWithReturn.has_return()

    exprWithoutReturn = pt.If(pt.Int(1), pt.Int(1), pt.Int(0))
    assert not exprWithoutReturn.has_return()

    exprSemiReturn = pt.If(
        pt.Int(1),
        pt.Return(pt.Int(1)),
        pt.App.globalPut(pt.Bytes("key"), pt.Bytes("value")),
    )
    assert not exprSemiReturn.has_return()


def test_if_int():
    args = [pt.Int(0), pt.Int(1), pt.Int(2)]
    expr = pt.If(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.uint64

    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseBlock, _ = args[2].__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseBlock)
    expected.setNextBlock(expectedBranch)
    end = pt.TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseBlock.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_bytes():
    args = [pt.Int(1), pt.Txn.sender(), pt.Txn.receiver()]
    expr = pt.If(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseBlock, _ = args[2].__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseBlock)
    expected.setNextBlock(expectedBranch)
    end = pt.TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseBlock.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_none():
    args = [pt.Int(0), pt.Pop(pt.Txn.sender()), pt.Pop(pt.Txn.receiver())]
    expr = pt.If(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.none

    expected, _ = args[0].__teal__(options)
    thenBlockStart, thenBlockEnd = args[1].__teal__(options)
    elseBlockStart, elseBlockEnd = args[2].__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlockStart)
    expectedBranch.setFalseBlock(elseBlockStart)
    expected.setNextBlock(expectedBranch)
    end = pt.TealSimpleBlock([])
    thenBlockEnd.setNextBlock(end)
    elseBlockEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_single():
    args = [pt.Int(1), pt.Pop(pt.Int(1))]
    expr = pt.If(args[0], args[1])
    assert expr.type_of() == pt.TealType.none

    expected, _ = args[0].__teal__(options)
    thenBlockStart, thenBlockEnd = args[1].__teal__(options)
    end = pt.TealSimpleBlock([])
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlockStart)
    expectedBranch.setFalseBlock(end)
    expected.setNextBlock(expectedBranch)
    thenBlockEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.If(pt.Int(0), pt.Txn.amount(), pt.Txn.sender())

    with pytest.raises(pt.TealTypeError):
        pt.If(pt.Txn.sender(), pt.Int(1), pt.Int(0))

    with pytest.raises(pt.TealTypeError):
        pt.If(pt.Int(0), pt.Txn.sender())

    with pytest.raises(pt.TealTypeError):
        pt.If(pt.Int(0), pt.Int(2))

    with pytest.raises(pt.TealCompileError):
        expr = pt.If(pt.Int(0))
        expr.__teal__(options)


def test_if_alt_int():
    args = [pt.Int(0), pt.Int(1), pt.Int(2)]
    expr = pt.If(args[0]).Then(args[1]).Else(args[2])
    assert expr.type_of() == pt.TealType.uint64

    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseBlock, _ = args[2].__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseBlock)
    expected.setNextBlock(expectedBranch)
    end = pt.TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseBlock.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_alt_bytes():
    args = [pt.Int(1), pt.Txn.sender(), pt.Txn.receiver()]
    expr = pt.If(args[0]).Then(args[1]).Else(args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseBlock, _ = args[2].__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseBlock)
    expected.setNextBlock(expectedBranch)
    end = pt.TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseBlock.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_alt_none():
    args = [pt.Int(0), pt.Pop(pt.Txn.sender()), pt.Pop(pt.Txn.receiver())]
    expr = pt.If(args[0]).Then(args[1]).Else(args[2])
    assert expr.type_of() == pt.TealType.none

    expected, _ = args[0].__teal__(options)
    thenBlockStart, thenBlockEnd = args[1].__teal__(options)
    elseBlockStart, elseBlockEnd = args[2].__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlockStart)
    expectedBranch.setFalseBlock(elseBlockStart)
    expected.setNextBlock(expectedBranch)
    end = pt.TealSimpleBlock([])
    thenBlockEnd.setNextBlock(end)
    elseBlockEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_elseif_syntax():
    args = [pt.Int(0), pt.Int(1), pt.Int(2), pt.Int(3), pt.Int(4)]
    expr = pt.If(args[0]).Then(args[1]).ElseIf(args[2]).Then(args[3]).Else(args[4])
    assert expr.type_of() == pt.TealType.uint64

    elseExpr = pt.If(args[2]).Then(args[3]).Else(args[4])
    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseStart, elseEnd = elseExpr.__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseStart)
    expected.setNextBlock(expectedBranch)
    end = pt.TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_elseif_multiple():
    args = [pt.Int(0), pt.Int(1), pt.Int(2), pt.Int(3), pt.Int(4), pt.Int(5), pt.Int(6)]
    expr = (
        pt.If(args[0])
        .Then(args[1])
        .ElseIf(args[2])
        .Then(args[3])
        .ElseIf(args[4])
        .Then(args[5])
        .Else(args[6])
    )
    assert expr.type_of() == pt.TealType.uint64

    elseIfExpr = pt.If(args[2], args[3], pt.If(args[4], args[5], args[6]))
    expected, _ = args[0].__teal__(options)
    thenBlock, _ = args[1].__teal__(options)
    elseStart, elseEnd = elseIfExpr.__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseStart)
    expected.setNextBlock(expectedBranch)
    end = pt.TealSimpleBlock([])
    thenBlock.setNextBlock(end)
    elseEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_if_invalid_alt_syntax():
    with pytest.raises(pt.TealCompileError):
        expr = pt.If(pt.Int(0)).ElseIf(pt.Int(1))
        expr.__teal__(options)

    with pytest.raises(pt.TealCompileError):
        expr = pt.If(pt.Int(0)).ElseIf(pt.Int(1)).Then(pt.Int(2))
        expr.__teal__(options)

    with pytest.raises(pt.TealCompileError):
        expr = pt.If(pt.Int(0)).Then(pt.Int(1)).ElseIf(pt.Int(2))
        expr.__teal__(options)

    with pytest.raises(pt.TealCompileError):
        expr = pt.If(pt.Int(0)).Then(pt.Int(1)).ElseIf(pt.Int(2))
        expr.__teal__(options)

    with pytest.raises(pt.TealTypeError):
        expr = pt.If(pt.Int(0)).Then(pt.Int(2))
        expr.type_of()

    with pytest.raises(pt.TealTypeError):
        expr = pt.If(pt.Int(0)).Then(pt.Pop(pt.Int(1)), pt.Int(2))
        expr.type_of()

    with pytest.raises(pt.TealInputError):
        pt.If(pt.Int(0)).Else(pt.Int(1)).Then(pt.Int(2))

    with pytest.raises(pt.TealInputError):
        expr = pt.If(pt.Int(0)).Else(pt.Int(1))
        expr.__teal__(options)

    with pytest.raises(pt.TealInputError):
        expr = pt.If(pt.Int(0)).Else(pt.Int(1)).Then(pt.Int(2))

    with pytest.raises(pt.TealInputError):
        expr = pt.If(pt.Int(0)).Else(pt.Int(1)).Else(pt.Int(2))

    with pytest.raises(pt.TealInputError):
        expr = pt.If(pt.Int(0), pt.Pop(pt.Int(1))).Else(pt.Int(2))


def test_if_alt_multi():
    args = [pt.Int(0), [pt.Pop(pt.Int(1)), pt.Int(2)], pt.Int(3)]
    expr = pt.If(args[0]).Then(*args[1]).Else(args[2])

    expected, _ = args[0].__teal__(options)
    thenBlockStart, thenBlockEnd = pt.Seq(*args[1]).__teal__(options)
    elseBlockStart, elseBlockEnd = args[2].__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlockStart)
    expectedBranch.setFalseBlock(elseBlockStart)
    expected.setNextBlock(expectedBranch)
    end = pt.TealSimpleBlock([])
    thenBlockEnd.setNextBlock(end)
    elseBlockEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_else_alt_multi():
    args = [pt.Int(0), pt.Int(1), [pt.Pop(pt.Int(2)), pt.Int(3)]]
    expr = pt.If(args[0]).Then(args[1]).Else(*args[2])

    expected, _ = args[0].__teal__(options)
    thenBlockStart, thenBlockEnd = args[1].__teal__(options)
    elseBlockStart, elseBlockEnd = pt.Seq(*args[2]).__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlockStart)
    expectedBranch.setFalseBlock(elseBlockStart)
    expected.setNextBlock(expectedBranch)
    end = pt.TealSimpleBlock([])
    thenBlockEnd.setNextBlock(end)
    elseBlockEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_elseif_multiple_with_multi():
    args = [
        pt.Int(0),
        [pt.Pop(pt.Int(1)), pt.Int(2)],
        pt.Int(3),
        [pt.Pop(pt.Int(4)), pt.Int(5)],
        pt.Int(6),
        [pt.Pop(pt.Int(7)), pt.Int(8)],
        [pt.Pop(pt.Int(9)), pt.Int(10)],
    ]
    expr = (
        pt.If(args[0])
        .Then(*args[1])
        .ElseIf(args[2])
        .Then(*args[3])
        .ElseIf(args[4])
        .Then(*args[5])
        .Else(*args[6])
    )

    elseIfExpr = pt.If(
        args[2], pt.Seq(args[3]), pt.If(args[4], pt.Seq(args[5]), pt.Seq(args[6]))
    )
    expected, _ = args[0].__teal__(options)
    thenBlock, thenBlockEnd = pt.Seq(args[1]).__teal__(options)
    elseStart, elseBlockEnd = elseIfExpr.__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(thenBlock)
    expectedBranch.setFalseBlock(elseStart)
    expected.setNextBlock(expectedBranch)
    end = pt.TealSimpleBlock([])
    thenBlockEnd.setNextBlock(end)
    elseBlockEnd.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected
