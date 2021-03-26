import pytest

from .. import *

def test_assert():
    expr = Assert(Int(1))
    assert expr.type_of() == TealType.none

    expected, _ = Int(1).__teal__()
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(TealSimpleBlock([]))
    expectedBranch.setFalseBlock(Err().__teal__()[0])
    expected.setNextBlock(expectedBranch)
    
    actual, _ = expr.__teal__()
    
    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected

def test_assert_invalid():
    with pytest.raises(TealTypeError):
        Assert(Txn.receiver())
