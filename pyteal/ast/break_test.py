import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

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

    items = [Int(1), Seq([Break()])]
    expr = While(items[0]).Do(items[1])
    actual, _ = expr.__teal__(options)

    options.currentLoop = expr
    start, _ = items[1].__teal__(options)

    assert len(options.breakBlocks) == 1
    assert start in options.breakBlocks
