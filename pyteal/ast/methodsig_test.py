import pytest

from pyteal.ast.methodsig import MethodSignature

import pyteal as pt


def test_method():
    expr = MethodSignature("add(uint64,uint64)uint64")
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [pt.TealOp(expr, pt.Op.method_signature, '"add(uint64,uint64)uint64"')]
    )
    actual, _ = expr.__teal__(pt.CompileOptions())
    assert expected == actual


def test_method_invalid():
    with pytest.raises(pt.TealInputError):
        MethodSignature(114514)

    with pytest.raises(pt.TealInputError):
        MethodSignature(['"m0()void"', '"m1()uint64"'])

    with pytest.raises(pt.TealInputError):
        MethodSignature("")
