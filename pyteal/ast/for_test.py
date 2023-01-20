import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_for_compiles():
    i = pt.ScratchVar()

    expr = pt.For(i.store(pt.Int(0)), pt.Int(1), i.store(i.load() + pt.Int(1))).Do(
        pt.App.globalPut(pt.Itob(pt.Int(0)), pt.Itob(pt.Int(2)))
    )
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()
    expr.__teal__(options)


def test_nested_for_compiles():
    i = pt.ScratchVar()
    expr = pt.For(i.store(pt.Int(0)), pt.Int(1), i.store(i.load() + pt.Int(1))).Do(
        pt.Seq(
            [
                pt.For(i.store(pt.Int(0)), pt.Int(1), i.store(i.load() + pt.Int(1))).Do(
                    pt.Seq([i.store(pt.Int(0))])
                )
            ]
        )
    )
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()


def test_continue_break():
    i = pt.ScratchVar()
    expr = pt.For(i.store(pt.Int(0)), pt.Int(1), i.store(i.load() + pt.Int(1))).Do(
        pt.Seq([pt.If(pt.Int(1), pt.Break(), pt.Continue())])
    )
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()
    expr.__teal__(options)


def test_for():
    i = pt.ScratchVar()
    items = [
        (i.store(pt.Int(0))),
        i.load() < pt.Int(10),
        i.store(i.load() + pt.Int(1)),
        pt.App.globalPut(pt.Itob(i.load()), i.load() * pt.Int(2)),
    ]
    expr = pt.For(items[0], items[1], items[2]).Do(pt.Seq([items[3]]))

    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected, varEnd = items[0].__teal__(options)
    condStart, condEnd = items[1].__teal__(options)
    stepStart, stepEnd = items[2].__teal__(options)
    do, doEnd = pt.Seq([items[3]]).__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    end = pt.TealSimpleBlock([])

    varEnd.setNextBlock(condStart)
    doEnd.setNextBlock(stepStart)

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    stepEnd.setNextBlock(condStart)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_for_continue():
    i = pt.ScratchVar()
    items = [
        (i.store(pt.Int(0))),
        i.load() < pt.Int(10),
        i.store(i.load() + pt.Int(1)),
        pt.If(i.load() < pt.Int(4), pt.Continue()),
        pt.App.globalPut(pt.Itob(i.load()), i.load() * pt.Int(2)),
    ]
    expr = pt.For(items[0], items[1], items[2]).Do(pt.Seq([items[3], items[4]]))

    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    options.enterLoop()

    expected, varEnd = items[0].__teal__(options)
    condStart, condEnd = items[1].__teal__(options)
    stepStart, stepEnd = items[2].__teal__(options)
    do, doEnd = pt.Seq([items[3], items[4]]).__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    end = pt.TealSimpleBlock([])

    doEnd.setNextBlock(stepStart)
    stepEnd.setNextBlock(condStart)

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    varEnd.setNextBlock(condStart)

    _, continueBlocks = options.exitLoop()

    for block in continueBlocks:
        block.setNextBlock(stepStart)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_for_break():
    i = pt.ScratchVar()
    items = [
        (i.store(pt.Int(0))),
        i.load() < pt.Int(10),
        i.store(i.load() + pt.Int(1)),
        pt.If(i.load() == pt.Int(6), pt.Break()),
        pt.App.globalPut(pt.Itob(i.load()), i.load() * pt.Int(2)),
    ]
    expr = pt.For(items[0], items[1], items[2]).Do(pt.Seq([items[3], items[4]]))

    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    options.enterLoop()

    expected, varEnd = items[0].__teal__(options)
    condStart, condEnd = items[1].__teal__(options)
    stepStart, stepEnd = items[2].__teal__(options)
    do, doEnd = pt.Seq([items[3], items[4]]).__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    end = pt.TealSimpleBlock([])

    doEnd.setNextBlock(stepStart)
    stepEnd.setNextBlock(condStart)

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    varEnd.setNextBlock(condStart)

    breakBlocks, _ = options.exitLoop()

    for block in breakBlocks:
        block.setNextBlock(end)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_invalid_for():
    with pytest.raises(TypeError):
        expr = pt.For()

    with pytest.raises(TypeError):
        expr = pt.For(pt.Int(2))

    with pytest.raises(TypeError):
        expr = pt.For(pt.Int(1), pt.Int(2))

    with pytest.raises(pt.TealTypeError):
        i = pt.ScratchVar()
        expr = pt.For(i.store(pt.Int(0)), pt.Int(1), pt.Int(2))
        expr.__teal__(options)

    with pytest.raises(pt.TealCompileError):
        i = pt.ScratchVar()
        expr = pt.For(i.store(pt.Int(0)), pt.Int(1), i.store(i.load() + pt.Int(1)))
        expr.type_of()

    with pytest.raises(pt.TealCompileError):
        i = pt.ScratchVar()
        expr = pt.For(i.store(pt.Int(0)), pt.Int(1), i.store(i.load() + pt.Int(1)))
        expr.__str__()

    with pytest.raises(pt.TealTypeError):
        i = pt.ScratchVar()
        expr = pt.For(i.store(pt.Int(0)), pt.Int(1), i.store(i.load() + pt.Int(1))).Do(
            pt.Int(0)
        )

    with pytest.raises(pt.TealTypeError):
        i = pt.ScratchVar()
        expr = pt.For(i.store(pt.Int(0)), pt.Int(1), i.store(i.load() + pt.Int(1))).Do(
            pt.Pop(pt.Int(1)), pt.Int(2)
        )

    with pytest.raises(pt.TealCompileError):
        expr = (
            pt.For(i.store(pt.Int(0)), pt.Int(1), i.store(i.load() + pt.Int(1)))
            .Do(pt.Continue())
            .Do(pt.Continue())
        )
        expr.__str__()


def test_for_multi():
    i = pt.ScratchVar()
    items = [
        (i.store(pt.Int(0))),
        i.load() < pt.Int(10),
        i.store(i.load() + pt.Int(1)),
        [pt.Pop(pt.Int(1)), pt.App.globalPut(pt.Itob(i.load()), i.load() * pt.Int(2))],
    ]
    expr = pt.For(items[0], items[1], items[2]).Do(*items[3])

    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected, varEnd = items[0].__teal__(options)
    condStart, condEnd = items[1].__teal__(options)
    stepStart, stepEnd = items[2].__teal__(options)
    do, doEnd = pt.Seq(items[3]).__teal__(options)
    expectedBranch = pt.TealConditionalBlock([])
    end = pt.TealSimpleBlock([])

    varEnd.setNextBlock(condStart)
    doEnd.setNextBlock(stepStart)

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    stepEnd.setNextBlock(condStart)

    actual, _ = expr.__teal__(options)

    assert actual == expected
