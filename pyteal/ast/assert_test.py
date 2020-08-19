import pytest

from .. import *

def test_assert():
    expr = Assert(Int(1))
    assert expr.type_of() == TealType.none
    teal = expr.__teal__()
    assert len(teal) == 4
    label = teal[3]
    assert isinstance(label, TealLabel)
    assert teal == [
        TealOp(Op.int, 1),
        TealOp(Op.bnz, label.label),
        TealOp(Op.err),
        label
    ]

def test_assert_invalid():
    with pytest.raises(TealTypeError):
        Assert(Txn.receiver())
