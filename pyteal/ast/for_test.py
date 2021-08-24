import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_for_compiles():
    i = ScratchVar()

    expr = For(i.store(Int(0)), Int(1), i.store(i.load() + Int(1))).Do(
        App.globalPut(Itob(Int(0)), Itob(Int(2)))
    )
    assert expr.type_of() == TealType.none
    assert not expr.has_return()
    expr.__teal__(options)


def test_nested_for_compiles():
    i = ScratchVar()
    expr = For(i.store(Int(0)), Int(1), i.store(i.load() + Int(1))).Do(
        Seq(
            [
                For(i.store(Int(0)), Int(1), i.store(i.load() + Int(1))).Do(
                    Seq([i.store(Int(0))])
                )
            ]
        )
    )
    assert expr.type_of() == TealType.none
    assert not expr.has_return()


def test_continue_break():
    i = ScratchVar()
    expr = For(i.store(Int(0)), Int(1), i.store(i.load() + Int(1))).Do(
        Seq([If(Int(1), Break(), Continue())])
    )
    assert expr.type_of() == TealType.none
    assert not expr.has_return()
    expr.__teal__(options)


def test_for():
    i = ScratchVar()
    items = [
        (i.store(Int(0))),
        i.load() < Int(10),
        i.store(i.load() + Int(1)),
        App.globalPut(Itob(i.load()), i.load() * Int(2)),
    ]
    expr = For(items[0], items[1], items[2]).Do(Seq([items[3]]))

    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected, varEnd = items[0].__teal__(options)
    condStart, condEnd = items[1].__teal__(options)
    stepStart, stepEnd = items[2].__teal__(options)
    do, doEnd = Seq([items[3]]).__teal__(options)
    expectedBranch = TealConditionalBlock([])
    end = TealSimpleBlock([])

    varEnd.setNextBlock(condStart)
    doEnd.setNextBlock(stepStart)

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    stepEnd.setNextBlock(condStart)

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_for_continue():
    i = ScratchVar()
    items = [
        (i.store(Int(0))),
        i.load() < Int(10),
        i.store(i.load() + Int(1)),
        If(i.load() < Int(4), Continue()),
        App.globalPut(Itob(i.load()), i.load() * Int(2)),
    ]
    expr = For(items[0], items[1], items[2]).Do(Seq([items[3], items[4]]))

    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    options.enterLoop()

    expected, varEnd = items[0].__teal__(options)
    condStart, condEnd = items[1].__teal__(options)
    stepStart, stepEnd = items[2].__teal__(options)
    do, doEnd = Seq([items[3], items[4]]).__teal__(options)
    expectedBranch = TealConditionalBlock([])
    end = TealSimpleBlock([])

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
    i = ScratchVar()
    items = [
        (i.store(Int(0))),
        i.load() < Int(10),
        i.store(i.load() + Int(1)),
        If(i.load() == Int(6), Break()),
        App.globalPut(Itob(i.load()), i.load() * Int(2)),
    ]
    expr = For(items[0], items[1], items[2]).Do(Seq([items[3], items[4]]))

    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    options.enterLoop()

    expected, varEnd = items[0].__teal__(options)
    condStart, condEnd = items[1].__teal__(options)
    stepStart, stepEnd = items[2].__teal__(options)
    do, doEnd = Seq([items[3], items[4]]).__teal__(options)
    expectedBranch = TealConditionalBlock([])
    end = TealSimpleBlock([])

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
        expr = For()

    with pytest.raises(TypeError):
        expr = For(Int(2))

    with pytest.raises(TypeError):
        expr = For(Int(1), Int(2))

    with pytest.raises(TealTypeError):
        i = ScratchVar()
        expr = For(i.store(Int(0)), Int(1), Int(2))
        expr.__teal__(options)

    with pytest.raises(TealCompileError):
        i = ScratchVar()
        expr = For(i.store(Int(0)), Int(1), i.store(i.load() + Int(1)))
        expr.type_of()

    with pytest.raises(TealCompileError):
        i = ScratchVar()
        expr = For(i.store(Int(0)), Int(1), i.store(i.load() + Int(1)))
        expr.__str__()

    with pytest.raises(TealTypeError):
        i = ScratchVar()
        expr = For(i.store(Int(0)), Int(1), i.store(i.load() + Int(1))).Do(Int(0))

    with pytest.raises(TealCompileError):
        expr = (
            For(i.store(Int(0)), Int(1), i.store(i.load() + Int(1)))
            .Do(Continue())
            .Do(Continue())
        )
        expr.__str__()
