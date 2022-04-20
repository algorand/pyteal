import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_continue_fail():
    with pytest.raises(pt.TealCompileError):
        pt.Continue().__teal__(options)

    with pytest.raises(pt.TealCompileError):
        pt.If(pt.Int(1), pt.Continue()).__teal__(options)

    with pytest.raises(pt.TealCompileError):
        pt.Seq([pt.Continue()]).__teal__(options)

    with pytest.raises(TypeError):
        pt.Continue(pt.Int(1))


def test_continue():

    expr = pt.Continue()

    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock([])

    options.enterLoop()
    actual, _ = expr.__teal__(options)
    breakBlocks, continueBlocks = options.exitLoop()

    assert actual == expected
    assert breakBlocks == []
    assert continueBlocks == [actual]
