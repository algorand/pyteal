import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_while_compiles():

    i = ScratchVar()
    expr = While(Int(2)).Do(Seq([i.store(Int(0))]))
    assert expr.type_of() == TealType.none
    expr.__teal__(options)


def test_nested_whiles_compile():
    i = ScratchVar()
    expr = While(Int(2)).Do(Seq([While(Int(2)).Do(Seq([i.store(Int(0))]))]))
    assert expr.type_of() == TealType.none


def test_continue_break():
    expr = While(Int(0)).Do(Seq([If(Int(1), Break(), Continue())]))
    assert expr.type_of() == TealType.none
    expr.__teal__(options)


def test_while():
    i = ScratchVar()
    i.store(Int(0))
    items = [i.load() < Int(2), [i.store(i.load() + Int(1))]]
    expr = While(items[0]).Do(Seq(items[1]))
    assert expr.type_of() == TealType.none

    expected, condEnd = items[0].__teal__(options)
    do, doEnd = Seq(items[1]).__teal__(options)
    expectedBranch = TealConditionalBlock([])
    end = TealSimpleBlock([])

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    doEnd.setNextBlock(expected)
    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_while_continue():
    i = ScratchVar()
    i.store(Int(0))
    items = [
        i.load() < Int(2),
        i.store(i.load() + Int(1)),
        If(i.load() == Int(1), Continue()),
    ]
    expr = While(items[0]).Do(Seq(items[1], items[2]))
    assert expr.type_of() == TealType.none

    options.currentLoop = expr
    expected, condEnd = items[0].__teal__(options)
    do, doEnd = Seq([items[1], items[2]]).__teal__(options)
    expectedBranch = TealConditionalBlock([])
    end = TealSimpleBlock([])

    for block in options.continueBlocks:
        block.setNextBlock(do)

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    doEnd.setNextBlock(expected)
    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_while_break():
    i = ScratchVar()
    i.store(Int(0))
    items = [
        i.load() < Int(2),
        i.store(i.load() + Int(1)),
        If(i.load() == Int(1), Break()),
    ]
    expr = While(items[0]).Do(Seq(items[1], items[2]))
    assert expr.type_of() == TealType.none

    options.currentLoop = expr
    expected, condEnd = items[0].__teal__(options)
    do, doEnd = Seq([items[1], items[2]]).__teal__(options)
    expectedBranch = TealConditionalBlock([])
    end = TealSimpleBlock([])

    for block in options.breakBlocks:
        block.setNextBlock(end)

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    doEnd.setNextBlock(expected)
    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_while_invalid():

    with pytest.raises(TypeError):
        expr = While()

    with pytest.raises(TealCompileError):
        expr = While(Int(2))
        expr.type_of()

    with pytest.raises(TealCompileError):
        expr = While(Int(2))
        expr.__teal__(options)

    with pytest.raises(TealCompileError):
        expr = While(Int(2))
        expr.type_of()

    with pytest.raises(TealCompileError):
        expr = While(Int(2))
        expr.__str__()

    with pytest.raises(TealTypeError):
        expr = While(Int(2)).Do(Int(2))
        expr.__str__()

    with pytest.raises(TealCompileError):
        expr = While(Int(0)).Do(Continue()).Do(Continue())
        expr.__str__()
