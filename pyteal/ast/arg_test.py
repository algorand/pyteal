import pytest

from .. import *

def test_arg():
    expr = Arg(0)
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.arg, 0)
    ]

def test_arg_invalid():
    with pytest.raises(TealInputError):
        Arg("k")

    with pytest.raises(TealInputError):
        Arg(-1)

    with pytest.raises(TealInputError):
        Arg(256)
