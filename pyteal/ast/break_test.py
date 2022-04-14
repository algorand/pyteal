import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_break_fail():

    with pytest.raises(pt.TealCompileError):
        pt.Break().__teal__(options)

    with pytest.raises(pt.TealCompileError):
        pt.If(pt.Int(1), pt.Break()).__teal__(options)

    with pytest.raises(pt.TealCompileError):
        pt.Seq([pt.Break()]).__teal__(options)

    with pytest.raises(TypeError):
        pt.Break(pt.Int(1))


def test_break():

    expr = pt.Break()

    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock([])

    options.enterLoop()
    actual, _ = expr.__teal__(options)
    breakBlocks, continueBlocks = options.exitLoop()

    assert actual == expected
    assert breakBlocks == [actual]
    assert continueBlocks == []
