import pytest

from .. import *

def test_err():
    expr = Err()
    assert expr.type_of() == TealType.none
    assert expr.__teal__() == [
        TealOp(Op.err)
    ]
