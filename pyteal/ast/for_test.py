import pytest

from .. import *
# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_for():
    i = ScratchVar()
    items = [(i.store(Int(0))),i.load() < Int(10), i.store(i.load() + Int(1)),App.globalPut(Itob(i.load()), i.load() * Int(2))]
    expr = For(items[0], items[1], items[2]).Do(Seq([
        items[3]

    ]))

    assert expr.type_of() == TealType.none
