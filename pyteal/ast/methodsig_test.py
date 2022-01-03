import pytest

from pyteal.ast.methodsig import MethodSignature

from .. import *


def test_method():
    expr = MethodSignature("add(uint64,uint64)uint64")
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(expr, Op.method_signature, '"add(uint64,uint64)uint64"')]
    )
    actual, _ = expr.__teal__(CompileOptions())
    assert expected == actual


def test_method_invalid():
    with pytest.raises(TealInputError):
        MethodSignature(114514)

    with pytest.raises(TealInputError):
        MethodSignature(['"m0()void"', '"m1()uint64"'])

    with pytest.raises(TealInputError):
        MethodSignature("")
