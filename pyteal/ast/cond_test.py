import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_cond_one_pred():
    expr = Cond([Int(1), Int(2)])
    assert expr.type_of() == TealType.uint64

    cond1, _ = Int(1).__teal__(options)
    pred1, _ = Int(2).__teal__(options)
    cond1Branch = TealConditionalBlock([])
    cond1.setNextBlock(cond1Branch)
    cond1Branch.setTrueBlock(pred1)
    cond1Branch.setFalseBlock(Err().__teal__(options)[0])
    pred1.setNextBlock(TealSimpleBlock([]))
    expected = cond1

    actual, _ = expr.__teal__(options)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_cond_two_pred():
    expr = Cond([Int(1), Bytes("one")], [Int(0), Bytes("zero")])
    assert expr.type_of() == TealType.bytes

    cond1, _ = Int(1).__teal__(options)
    pred1, _ = Bytes("one").__teal__(options)
    cond1Branch = TealConditionalBlock([])
    cond2, _ = Int(0).__teal__(options)
    pred2, _ = Bytes("zero").__teal__(options)
    cond2Branch = TealConditionalBlock([])
    end = TealSimpleBlock([])

    cond1.setNextBlock(cond1Branch)
    cond1Branch.setTrueBlock(pred1)
    cond1Branch.setFalseBlock(cond2)
    pred1.setNextBlock(end)

    cond2.setNextBlock(cond2Branch)
    cond2Branch.setTrueBlock(pred2)
    cond2Branch.setFalseBlock(Err().__teal__(options)[0])
    pred2.setNextBlock(end)

    expected = cond1

    actual, _ = expr.__teal__(options)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_cond_three_pred():
    expr = Cond([Int(1), Int(2)], [Int(3), Int(4)], [Int(5), Int(6)])
    assert expr.type_of() == TealType.uint64

    cond1, _ = Int(1).__teal__(options)
    pred1, _ = Int(2).__teal__(options)
    cond1Branch = TealConditionalBlock([])
    cond2, _ = Int(3).__teal__(options)
    pred2, _ = Int(4).__teal__(options)
    cond2Branch = TealConditionalBlock([])
    cond3, _ = Int(5).__teal__(options)
    pred3, _ = Int(6).__teal__(options)
    cond3Branch = TealConditionalBlock([])
    end = TealSimpleBlock([])

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
    cond3Branch.setFalseBlock(Err().__teal__(options)[0])
    pred3.setNextBlock(end)

    expected = cond1

    actual, _ = expr.__teal__(options)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_cond_has_return():
    exprWithReturn = Cond([Int(1), Return(Int(1))], [Int(0), Return(Int(0))])
    assert exprWithReturn.has_return()

    exprWithoutReturn = Cond([Int(1), Bytes("one")], [Int(0), Bytes("zero")])
    assert not exprWithoutReturn.has_return()

    exprSemiReturn = Cond(
        [Int(1), Return(Int(1))], [Int(0), App.globalPut(Bytes("key"), Bytes("value"))]
    )
    assert not exprSemiReturn.has_return()


def test_cond_invalid():
    with pytest.raises(TealInputError):
        Cond()

    with pytest.raises(TealInputError):
        Cond([])

    with pytest.raises(TealTypeError):
        Cond([Int(1), Int(2)], [Int(2), Txn.receiver()])

    with pytest.raises(TealTypeError):
        Cond([Arg(0), Int(2)])
