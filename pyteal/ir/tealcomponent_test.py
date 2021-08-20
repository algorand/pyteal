import pytest

from .. import *


def test_EqualityContext():
    expr1 = Int(1)
    expr2 = Int(1)

    op1 = TealOp(expr1, Op.int, 1)
    op2 = TealOp(expr2, Op.int, 1)

    assert op1 == op1
    assert op2 == op2
    assert op1 != op2
    assert op2 != op1

    with TealComponent.Context.ignoreExprEquality():
        assert op1 == op1
        assert op2 == op2
        assert op1 == op2
        assert op2 == op1
