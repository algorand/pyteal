import pytest

from .. import *


def test_arg():
    expr = Arg(0)
    assert expr.type_of() == TealType.bytes
    expected = TealSimpleBlock([TealOp(expr, Op.arg, 0)])
    actual, _ = expr.__teal__(CompileOptions())
    assert actual == expected


def test_arg_invalid():
    with pytest.raises(TealInputError):
        Arg("k")

    with pytest.raises(TealInputError):
        Arg(-1)

    with pytest.raises(TealInputError):
        Arg(256)
