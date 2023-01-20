import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_cond_one_pred():
    expr = pt.Cond([pt.Int(1), pt.Int(2)])
    assert expr.type_of() == pt.TealType.uint64

    cond1, _ = pt.Int(1).__teal__(options)
    pred1, _ = pt.Int(2).__teal__(options)
    cond1Branch = pt.TealConditionalBlock([])
    cond1.setNextBlock(cond1Branch)
    cond1Branch.setTrueBlock(pred1)
    cond1Branch.setFalseBlock(pt.Err().__teal__(options)[0])
    pred1.setNextBlock(pt.TealSimpleBlock([]))
    expected = cond1

    actual, _ = expr.__teal__(options)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_cond_two_pred():
    expr = pt.Cond([pt.Int(1), pt.Bytes("one")], [pt.Int(0), pt.Bytes("zero")])
    assert expr.type_of() == pt.TealType.bytes

    cond1, _ = pt.Int(1).__teal__(options)
    pred1, _ = pt.Bytes("one").__teal__(options)
    cond1Branch = pt.TealConditionalBlock([])
    cond2, _ = pt.Int(0).__teal__(options)
    pred2, _ = pt.Bytes("zero").__teal__(options)
    cond2Branch = pt.TealConditionalBlock([])
    end = pt.TealSimpleBlock([])

    cond1.setNextBlock(cond1Branch)
    cond1Branch.setTrueBlock(pred1)
    cond1Branch.setFalseBlock(cond2)
    pred1.setNextBlock(end)

    cond2.setNextBlock(cond2Branch)
    cond2Branch.setTrueBlock(pred2)
    cond2Branch.setFalseBlock(pt.Err().__teal__(options)[0])
    pred2.setNextBlock(end)

    expected = cond1

    actual, _ = expr.__teal__(options)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_cond_three_pred():
    expr = pt.Cond(
        [pt.Int(1), pt.Int(2)], [pt.Int(3), pt.Int(4)], [pt.Int(5), pt.Int(6)]
    )
    assert expr.type_of() == pt.TealType.uint64

    cond1, _ = pt.Int(1).__teal__(options)
    pred1, _ = pt.Int(2).__teal__(options)
    cond1Branch = pt.TealConditionalBlock([])
    cond2, _ = pt.Int(3).__teal__(options)
    pred2, _ = pt.Int(4).__teal__(options)
    cond2Branch = pt.TealConditionalBlock([])
    cond3, _ = pt.Int(5).__teal__(options)
    pred3, _ = pt.Int(6).__teal__(options)
    cond3Branch = pt.TealConditionalBlock([])
    end = pt.TealSimpleBlock([])

    cond1.setNextBlock(cond1Branch)
    cond1Branch.setTrueBlock(pred1)
    cond1Branch.setFalseBlock(cond2)
    pred1.setNextBlock(end)

    cond2.setNextBlock(cond2Branch)
    cond2Branch.setTrueBlock(pred2)
    cond2Branch.setFalseBlock(cond3)
    pred2.setNextBlock(end)

    cond3.setNextBlock(cond3Branch)
    cond3Branch.setTrueBlock(pred3)
    cond3Branch.setFalseBlock(pt.Err().__teal__(options)[0])
    pred3.setNextBlock(end)

    expected = cond1

    actual, _ = expr.__teal__(options)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_cond_has_return():
    exprWithReturn = pt.Cond(
        [pt.Int(1), pt.Return(pt.Int(1))], [pt.Int(0), pt.Return(pt.Int(0))]
    )
    assert exprWithReturn.has_return()

    exprWithoutReturn = pt.Cond(
        [pt.Int(1), pt.Bytes("one")], [pt.Int(0), pt.Bytes("zero")]
    )
    assert not exprWithoutReturn.has_return()

    exprSemiReturn = pt.Cond(
        [pt.Int(1), pt.Return(pt.Int(1))],
        [pt.Int(0), pt.App.globalPut(pt.Bytes("key"), pt.Bytes("value"))],
    )
    assert not exprSemiReturn.has_return()


def test_cond_invalid():
    with pytest.raises(pt.TealInputError):
        pt.Cond()

    with pytest.raises(pt.TealInputError):
        pt.Cond([])

    with pytest.raises(pt.TealInputError):
        pt.Cond([pt.Int(1)], [pt.Int(2), pt.Pop(pt.Txn.receiver())])

    with pytest.raises(pt.TealTypeError):
        pt.Cond([pt.Int(1), pt.Int(2)], [pt.Int(2), pt.Txn.receiver()])

    with pytest.raises(pt.TealTypeError):
        pt.Cond([pt.Arg(0), pt.Int(2)])

    with pytest.raises(pt.TealTypeError):
        pt.Cond([pt.Int(1), pt.Int(2)], [pt.Int(2), pt.Pop(pt.Int(2))])

    with pytest.raises(pt.TealTypeError):
        pt.Cond([pt.Int(1), pt.Pop(pt.Int(1))], [pt.Int(2), pt.Int(2)])


def test_cond_two_pred_multi():
    args = [
        pt.Int(1),
        [pt.Pop(pt.Int(1)), pt.Bytes("one")],
        pt.Int(0),
        [pt.Pop(pt.Int(2)), pt.Bytes("zero")],
    ]
    expr = pt.Cond(
        [args[0]] + args[1],
        [args[2]] + args[3],
    )
    assert expr.type_of() == pt.TealType.bytes

    cond1, _ = args[0].__teal__(options)
    pred1, pred1End = pt.Seq(args[1]).__teal__(options)
    cond1Branch = pt.TealConditionalBlock([])
    cond2, _ = args[2].__teal__(options)
    pred2, pred2End = pt.Seq(args[3]).__teal__(options)
    cond2Branch = pt.TealConditionalBlock([])
    end = pt.TealSimpleBlock([])

    cond1.setNextBlock(cond1Branch)
    cond1Branch.setTrueBlock(pred1)
    cond1Branch.setFalseBlock(cond2)
    pred1End.setNextBlock(end)

    cond2.setNextBlock(cond2Branch)
    cond2Branch.setTrueBlock(pred2)
    cond2Branch.setFalseBlock(pt.Err().__teal__(options)[0])
    pred2End.setNextBlock(end)

    expected = cond1

    actual, _ = expr.__teal__(options)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected
