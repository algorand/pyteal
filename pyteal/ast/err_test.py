import pytest

from .. import *

def test_err():
    expr = Err()
    assert expr.type_of() == TealType.none
    expected = TealSimpleBlock([
        TealOp(Op.err)
    ])
    actual, _ = expr.__teal__()
    assert actual == expected
