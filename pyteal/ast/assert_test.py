import pytest

import pyteal as pt

avm2Options = pt.CompileOptions(version=2)
avm3Options = pt.CompileOptions(version=3)


def test_teal_2_assert():
    arg = pt.Int(1)
    expr = pt.Assert(arg)
    assert expr.type_of() == pt.TealType.none

    expected, _ = arg.__teal__(avm2Options)
    expectedBranch = pt.TealConditionalBlock([])
    expectedBranch.setTrueBlock(pt.TealSimpleBlock([]))
    expectedBranch.setFalseBlock(pt.Err().__teal__(avm2Options)[0])
    expected.setNextBlock(expectedBranch)

    actual, _ = expr.__teal__(avm2Options)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_teal_2_assert_multi():
    args = [pt.Int(1), pt.Int(2)]
    expr = pt.Assert(*args)
    assert expr.type_of() == pt.TealType.none

    firstAssert = pt.Assert(args[0])
    secondAssert = pt.Assert(args[1])

    expected, _ = pt.Seq(firstAssert, secondAssert).__teal__(avm2Options)

    actual, _ = expr.__teal__(avm2Options)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_teal_3_assert():
    arg = pt.Int(1)
    expr = pt.Assert(arg)
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 1), pt.TealOp(expr, pt.Op.assert_)]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_teal_3_assert_multi():
    args = [pt.Int(1), pt.Int(2)]
    expr = pt.Assert(*args)
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [pt.TealOp(args[0], pt.Op.int, 1), pt.TealOp(expr, pt.Op.assert_)]
        + [pt.TealOp(args[1], pt.Op.int, 2), pt.TealOp(expr, pt.Op.assert_)]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_assert_comment():
    comment = "Make sure 1 is true"
    expr = pt.Assert(pt.Int(1), comment=comment)
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.comment, comment),
            pt.TealOp(None, pt.Op.assert_),
        ]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_assert_comment_multi():
    comment = "Make sure numbers > 0 are true"
    expr = pt.Assert(pt.Int(1), pt.Int(2), pt.Int(3), comment=comment)
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.comment, comment),
            pt.TealOp(None, pt.Op.assert_),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.comment, comment),
            pt.TealOp(None, pt.Op.assert_),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.comment, comment),
            pt.TealOp(None, pt.Op.assert_),
        ]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_assert_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Assert(pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Assert(pt.Int(1), pt.Txn.receiver())
