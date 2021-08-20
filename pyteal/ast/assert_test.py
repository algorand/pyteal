import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

teal2Options = CompileOptions(version=2)
teal3Options = CompileOptions(version=3)


def test_teal_2_assert():
    arg = Int(1)
    expr = Assert(arg)
    assert expr.type_of() == TealType.none

    expected, _ = arg.__teal__(teal2Options)
    expectedBranch = TealConditionalBlock([])
    expectedBranch.setTrueBlock(TealSimpleBlock([]))
    expectedBranch.setFalseBlock(Err().__teal__(teal2Options)[0])
    expected.setNextBlock(expectedBranch)

    actual, _ = expr.__teal__(teal2Options)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_teal_3_assert():
    arg = Int(1)
    expr = Assert(arg)
    assert expr.type_of() == TealType.none

    expected = TealSimpleBlock([TealOp(arg, Op.int, 1), TealOp(expr, Op.assert_)])

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_assert_invalid():
    with pytest.raises(TealTypeError):
        Assert(Txn.receiver())
