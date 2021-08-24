import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

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

    items = [Int(1), Seq([Continue()])]
    expr = While(items[0]).Do(items[1])
    actual, _ = expr.__teal__(options)

    options.currentLoop = expr
    start, _ = items[1].__teal__(options)

    assert len(options.continueBlocks) == 1
    assert start in options.continueBlocks
