import pytest

from .. import *

options = CompileOptions()


def test_break_fail():

    with pytest.raises(TealCompileError):
        Break().__teal__(options)

    with pytest.raises(TealCompileError):
        If(Int(1), Break()).__teal__(options)

    with pytest.raises(TealCompileError):
        Seq([Break()]).__teal__(options)

    with pytest.raises(TypeError):
        Break(Int(1))


def test_break():

    expr = Break()

    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock([])

    options.enterLoop()
    actual, _ = expr.__teal__(options)
    breakBlocks, continueBlocks = options.exitLoop()

    assert actual == expected
    assert breakBlocks == [actual]
    assert continueBlocks == []
