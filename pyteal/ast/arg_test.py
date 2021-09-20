import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

teal2Options = CompileOptions(version=2)
teal4Options = CompileOptions(version=4)
teal5Options = CompileOptions(version=5)


def test_arg_static():
    for i in range(256):
        expr = Arg(i)
        assert expr.type_of() == TealType.bytes
        assert not expr.has_return()

        expected = TealSimpleBlock([TealOp(expr, Op.arg, i)])

        actual, _ = expr.__teal__(teal2Options)
        assert actual == expected


def test_arg_dynamic():
    i = Int(7)
    expr = Arg(i)
    assert expr.type_of() == TealType.bytes
    assert not expr.has_return()

    expected = TealSimpleBlock([TealOp(i, Op.int, 7), TealOp(expr, Op.args)])

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_arg_invalid():
    with pytest.raises(TealTypeError):
        Arg(Bytes("k"))

    with pytest.raises(TealInputError):
        Arg(-1)

    with pytest.raises(TealInputError):
        Arg(256)
