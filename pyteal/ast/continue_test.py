import pytest

from .. import *

options = CompileOptions()


def test_continue_fail():
    with pytest.raises(TealCompileError):
        Continue().__teal__(options)

    with pytest.raises(TealCompileError):
        If(Int(1), Continue()).__teal__(options)

    with pytest.raises(TealCompileError):
        Seq([Continue()]).__teal__(options)

    with pytest.raises(TypeError):
        Continue(Int(1))


def test_continue():

    expr = Continue()

    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock([])

    options.enterLoop()
    actual, _ = expr.__teal__(options)
    breakBlocks, continueBlocks = options.exitLoop()

    assert actual == expected
    assert breakBlocks == []
    assert continueBlocks == [actual]
