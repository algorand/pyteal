import pyteal as pt
from pyteal.ast.maybe_test import assert_MaybeValue_equality

options = pt.CompileOptions()
teal4Options = pt.CompileOptions(version=4)
teal5Options = pt.CompileOptions(version=5)
teal6Options = pt.CompileOptions(version=6)


def test_acct_param_balance_valid():
    arg = pt.Int(1)
    expr = pt.AccountParam.balance(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.acct_params_get, "AcctBalance"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal6Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_acct_param_min_balance_valid():
    arg = pt.Int(0)
    expr = pt.AccountParam.minBalance(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.acct_params_get, "AcctMinBalance"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal6Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_acct_param_auth_addr_valid():
    arg = pt.Int(1)
    expr = pt.AccountParam.authAddr(arg)
    assert expr.type_of() == pt.TealType.none
    assert expr.value().type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.acct_params_get, "AcctAuthAddr"),
            pt.TealOp(None, pt.Op.store, expr.slotOk),
            pt.TealOp(None, pt.Op.store, expr.slotValue),
        ]
    )

    actual, _ = expr.__teal__(teal6Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_AccountParamObject():
    for account in (
        pt.Int(7),
        pt.Addr("QSA6K5MNJPEGO5SDSWXBM3K4UEI3Q2NCPS2OUXVJI5QPCHMVI27MFRSHKI"),
    ):
        obj = pt.AccountParamObject(account)

        assert obj._account is account

        assert_MaybeValue_equality(
            obj.balance(), pt.AccountParam.balance(account), teal6Options
        )
        assert_MaybeValue_equality(
            obj.min_balance(), pt.AccountParam.minBalance(account), teal6Options
        )
        assert_MaybeValue_equality(
            obj.auth_address(), pt.AccountParam.authAddr(account), teal6Options
        )
