import pytest

from .. import *
# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()

def test_while():
    i=ScratchVar()
    i.store(Int(0))
    items=[i.load()<Int(2), [i.store(i.load() + Int(1))]]
    expr=While(items[0]).Do(
            Seq(items[1])
            )
    assert expr.type_of() == TealType.none
    
    expected, condEnd= items[0].__teal__(options)
    do, doEnd = Seq(items[1]).__teal__(options)
    expectedBranch = TealConditionalBlock([])
    end = TealSimpleBlock([])

    expectedBranch.setTrueBlock(do)
    expectedBranch.setFalseBlock(end)
    condEnd.setNextBlock(expectedBranch)
    doEnd.setNextBlock(expected)
    actual, _ = expr.__teal__(options)

    assert actual == expected