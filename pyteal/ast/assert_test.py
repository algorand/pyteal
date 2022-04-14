import pytest

import pyteal as pt

teal2Options = pt.CompileOptions(version=2)
teal3Options = pt.CompileOptions(version=3)


def test_teal_2_assert():
    arg = pt.Int(1)
    expr = pt.Assert(arg)
    assert expr.type_of() == pt.TealType.none

    expected, _ = arg.__teal__(teal2Options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(pt.TealSimpleBlock([]))
    expectedBranch.setFalseBlock(pt.Err().__teal__(teal2Options)[0])
    expected.setNextBlock(expectedBranch)

    actual, _ = expr.__teal__(teal2Options)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_teal_3_assert():
    arg = pt.Int(1)
    expr = pt.Assert(arg)
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 1), pt.TealOp(expr, pt.Op.assert_)]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_assert_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Assert(pt.Txn.receiver())
