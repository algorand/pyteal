import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_while_compiles():

    i = pt.ScratchVar()
    expr = pt.While(pt.Int(2)).Do(pt.Seq([i.store(pt.Int(0))]))
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()
    expr.__teal__(options)


def test_nested_whiles_compile():
    i = pt.ScratchVar()
    expr = pt.While(pt.Int(2)).Do(
        pt.Seq([pt.While(pt.Int(2)).Do(pt.Seq([i.store(pt.Int(0))]))])
    )
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()


def test_continue_break():
    expr = pt.While(pt.Int(0)).Do(pt.Seq([pt.If(pt.Int(1), pt.Break(), pt.Continue())]))
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()
    expr.__teal__(options)


def test_while():
    i = pt.ScratchVar()
    i.store(pt.Int(0))
    items = [i.load() < pt.Int(2), [i.store(i.load() + pt.Int(1))]]
    expr = pt.While(items[0]).Do(pt.Seq(items[1]))
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected, condEnd = items[0].__teal__(options)
    do, doEnd = pt.Seq(items[1]).__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    end = pt.TealSimpleBlock([])

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    doEnd.setNextBlock(expected)
    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_while_continue():
    i = pt.ScratchVar()
    i.store(pt.Int(0))
    items = [
        i.load() < pt.Int(2),
        i.store(i.load() + pt.Int(1)),
        pt.If(i.load() == pt.Int(1), pt.Continue()),
    ]
    expr = pt.While(items[0]).Do(pt.Seq(items[1], items[2]))
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    options.enterLoop()

    expected, condEnd = items[0].__teal__(options)
    do, doEnd = pt.Seq([items[1], items[2]]).__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    end = pt.TealSimpleBlock([])

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    doEnd.setNextBlock(expected)

    _, continueBlocks = options.exitLoop()

    for block in continueBlocks:
        block.setNextBlock(do)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_while_break():
    i = pt.ScratchVar()
    i.store(pt.Int(0))
    items = [
        i.load() < pt.Int(2),
        i.store(i.load() + pt.Int(1)),
        pt.If(i.load() == pt.Int(1), pt.Break()),
    ]
    expr = pt.While(items[0]).Do(pt.Seq(items[1], items[2]))
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    options.enterLoop()

    expected, condEnd = items[0].__teal__(options)
    do, doEnd = pt.Seq([items[1], items[2]]).__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    end = pt.TealSimpleBlock([])

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    doEnd.setNextBlock(expected)

    breakBlocks, _ = options.exitLoop()

    for block in breakBlocks:
        block.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_while_invalid():

    with pytest.raises(TypeError):
        expr = pt.While()

    with pytest.raises(pt.TealCompileError):
        expr = pt.While(pt.Int(2))
        expr.type_of()

    with pytest.raises(pt.TealCompileError):
        expr = pt.While(pt.Int(2))
        expr.__teal__(options)

    with pytest.raises(pt.TealCompileError):
        expr = pt.While(pt.Int(2))
        expr.type_of()

    with pytest.raises(pt.TealCompileError):
        expr = pt.While(pt.Int(2))
        expr.__str__()

    with pytest.raises(pt.TealTypeError):
        expr = pt.While(pt.Int(2)).Do(pt.Int(2))

    with pytest.raises(pt.TealTypeError):
        expr = pt.While(pt.Int(2)).Do(pt.Pop(pt.Int(2)), pt.Int(2))

    with pytest.raises(pt.TealCompileError):
        expr = pt.While(pt.Int(0)).Do(pt.Continue()).Do(pt.Continue())
        expr.__str__()


def test_while_multi():
    i = pt.ScratchVar()
    i.store(pt.Int(0))
    items = [i.load() < pt.Int(2), [pt.Pop(pt.Int(1)), i.store(i.load() + pt.Int(1))]]
    expr = pt.While(items[0]).Do(*items[1])
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected, condEnd = items[0].__teal__(options)
    do, doEnd = pt.Seq(items[1]).__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    end = pt.TealSimpleBlock([])

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    doEnd.setNextBlock(expected)
    actual, _ = expr.__teal__(options)

    assert actual == expected
