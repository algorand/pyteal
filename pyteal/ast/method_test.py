import pytest

from pyteal.ast.method import Method

from .. import *


def test_method():
    expr = Method("add(uint64,uint64)uint64")
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.method, "\"add(uint64,uint64)uint64\"")])
    actual, _ = expr.__teal__(CompileOptions())
    assert expected == actual


def test_method_invalid():
    with pytest.raises(TealInputError):
        Method(114514)

    with pytest.raises(TealInputError):
        Method(["\"m0()void\"", "\"m1()uint64\""])

    with pytest.raises(TealInputError):
        Method("")
