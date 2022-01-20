import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()
teal4Options = CompileOptions(version=4)
teal5Options = CompileOptions(version=5)
teal6Options = CompileOptions(version=6)


def test_acct_param_balance_valid():
    arg = Int(1)
    expr = AccountParam.balance(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.acct_params_get, "AcctBalance"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal6Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_acct_param_min_balance_valid():
    arg = Int(0)
    expr = AccountParam.minBalance(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 0),
            TealOp(expr, Op.acct_params_get, "AcctMinBalance"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal6Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_acct_param_auth_addr_valid():
    arg = Int(1)
    expr = AccountParam.authAddr(arg)
    assert expr.type_of() == TealType.none
    assert expr.value().type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 1),
            TealOp(expr, Op.acct_params_get, "AcctAuthAddr"),
            TealOp(None, Op.store, expr.slotOk),
            TealOp(None, Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal6Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected
