import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import MAX_GROUP_SIZE, CompileOptions

teal3Options = CompileOptions(version=3)
teal4Options = CompileOptions(version=4)


def test_gaid_teal_3():
    with pytest.raises(TealInputError):
        GeneratedID(0).__teal__(teal3Options)


def test_gaid():
    expr = GeneratedID(0)
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.gaid, 0)])

    actual, _ = expr.__teal__(teal4Options)

    assert actual == expected


def test_gaid_invalid():
    with pytest.raises(TealInputError):
        GeneratedID(-1)

    with pytest.raises(TealInputError):
        GeneratedID(MAX_GROUP_SIZE)


def test_gaid_dynamic_teal_3():
    with pytest.raises(TealInputError):
        GeneratedID(Int(0)).__teal__(teal3Options)


def test_gaid_dynamic():
    arg = Int(0)
    expr = GeneratedID(arg)
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(arg, Op.int, 0), TealOp(expr, Op.gaids)])

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gaid_dynamic_invalid():
    with pytest.raises(TealTypeError):
        GeneratedID(Bytes("index"))
