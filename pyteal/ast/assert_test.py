import pytest

from .. import *

def test_assert():
    expr = Assert(Int(1))
    assert expr.type_of() == TealType.none

    expected, _ = Int(1).__teal__()
    expected.setFalseBlock(Err().__teal__()[0])
    
    actual, _ = expr.__teal__()
    actual.trim()
    
    assert actual == expected

def test_assert_invalid():
    with pytest.raises(TealTypeError):
        Assert(Txn.receiver())
