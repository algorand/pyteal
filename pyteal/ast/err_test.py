import pytest

from .. import *


def test_err():
    expr = Err()
    assert expr.type_of() == TealType.none
    assert expr.has_return()
    expected = TealSimpleBlock([TealOp(expr, Op.err)])
    actual, _ = expr.__teal__(CompileOptions())
    assert actual == expected
