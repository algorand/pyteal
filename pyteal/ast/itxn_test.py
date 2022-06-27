import pytest

import pyteal as pt
from pyteal.ast.txn import TxnField, TxnType
from pyteal.types import types_match

teal4Options = pt.CompileOptions(version=4)
teal5Options = pt.CompileOptions(version=5)
teal6Options = pt.CompileOptions(version=6)


def test_InnerTxnBuilder_Begin():
    expr = pt.InnerTxnBuilder.Begin()
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.itxn_begin)])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(teal4Options)


def test_InnerTxnBuilder_Submit():
    expr = pt.InnerTxnBuilder.Submit()
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.itxn_submit)])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(teal4Options)


def test_InnerTxnBuilder_Next():
    expr = pt.InnerTxnBuilder.Next()
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.itxn_next)])

    actual, _ = expr.__teal__(teal6Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(teal5Options)


def test_InnerTxnBuilder_SetField():
    for field in pt.TxnField:
        if field.is_array:
            with pytest.raises(pt.TealInputError):
                pt.InnerTxnBuilder.SetField(field, pt.Int(0))
            continue

        for value, opArgs in (
            (pt.Int(0), (pt.Op.int, 0)),
            (pt.Bytes("value"), (pt.Op.byte, '"value"')),
        ):
            assert field.type_of() in (pt.TealType.uint64, pt.TealType.bytes)

            if not types_match(field.type_of(), value.type_of()):
                with pytest.raises(pt.TealTypeError):
                    pt.InnerTxnBuilder.SetField(field, value)
                continue

            expr = pt.InnerTxnBuilder.SetField(field, value)
            assert expr.type_of() == pt.TealType.none
            assert not expr.has_return()

            expected = pt.TealSimpleBlock(
                [
                    pt.TealOp(value, *opArgs),
                    pt.TealOp(expr, pt.Op.itxn_field, field.arg_name),
                ]
            )

            actual, _ = expr.__teal__(teal5Options)
            actual.addIncoming()
            actual = pt.TealBlock.NormalizeBlocks(actual)

            assert actual == expected

            with pytest.raises(pt.TealInputError):
                expr.__teal__(teal4Options)


def test_InnerTxnBuilder_SetFields():
    cases = (
        ({}, pt.Seq()),
        (
            {pt.TxnField.amount: pt.Int(5)},
            pt.InnerTxnBuilder.SetField(pt.TxnField.amount, pt.Int(5)),
        ),
        (
            {
                pt.TxnField.type_enum: pt.TxnType.Payment,
                pt.TxnField.close_remainder_to: pt.Txn.sender(),
            },
            pt.Seq(
                pt.InnerTxnBuilder.SetField(pt.TxnField.type_enum, pt.TxnType.Payment),
                pt.InnerTxnBuilder.SetField(
                    pt.TxnField.close_remainder_to, pt.Txn.sender()
                ),
            ),
        ),
    )

    for fields, expectedExpr in cases:
        expr = pt.InnerTxnBuilder.SetFields(fields)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        expected, _ = expectedExpr.__teal__(teal5Options)
        expected.addIncoming()
        expected = pt.TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(teal5Options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected

        if len(fields) != 0:
            with pytest.raises(pt.TealInputError):
                expr.__teal__(teal4Options)


ITXN_METHOD_CASES = (
    (
        pt.Int(1),
        "add(uint64,uint64)void",
        [pt.Itob(pt.Int(1)), pt.Itob(pt.Int(1))],
        {TxnField.fee: pt.Int(0)},
        pt.Seq(
            pt.InnerTxnBuilder.SetFields(
                {
                    pt.TxnField.type_enum: TxnType.ApplicationCall,
                    pt.TxnField.application_id: pt.Int(1),
                    pt.TxnField.application_args: [
                        pt.MethodSignature("add(uint64,uint64)void"),
                        pt.Itob(pt.Int(1)),
                        pt.Itob(pt.Int(1)),
                    ],
                    pt.TxnField.fee: pt.Int(0),
                }
            ),
        ),
    ),
    (
        pt.Int(1),
        "add(uint64,uint64)void",
        [pt.abi.Uint64(), pt.abi.Uint64()],
        {TxnField.fee: pt.Int(0)},
        pt.Seq(
            pt.InnerTxnBuilder.SetFields(
                {
                    pt.TxnField.type_enum: TxnType.ApplicationCall,
                    pt.TxnField.application_id: pt.Int(1),
                    pt.TxnField.application_args: [
                        pt.MethodSignature("add(uint64,uint64)void"),
                        pt.abi.Uint64().encode(),
                        pt.abi.Uint64().encode(),
                    ],
                    pt.TxnField.fee: pt.Int(0),
                }
            ),
        ),
    ),
    (
        pt.Int(1),
        "add(application,asset,account)void",
        [pt.abi.Application(), pt.abi.Asset(), pt.abi.Account()],
        {TxnField.fee: pt.Int(0)},
        pt.Seq(
            pt.InnerTxnBuilder.SetFields(
                {
                    pt.TxnField.type_enum: TxnType.ApplicationCall,
                    pt.TxnField.application_id: pt.Int(1),
                    pt.TxnField.accounts: [pt.abi.Account().address()],
                    pt.TxnField.applications: [pt.abi.Application().application_id()],
                    pt.TxnField.assets: [pt.abi.Asset().asset_id()],
                    pt.TxnField.application_args: [
                        pt.MethodSignature("add(application,asset,account)void"),
                        pt.Bytes(b"\x01"),
                        pt.Bytes(b"\x00"),
                        pt.Bytes(b"\x01"),
                    ],
                    pt.TxnField.fee: pt.Int(0),
                }
            ),
        ),
    ),
    (
        pt.Int(1),
        "add(pay,txn,appl)void",
        [
            {TxnField.type_enum: TxnType.Payment},
            {TxnField.type_enum: TxnType.AssetTransfer},
            {TxnField.type_enum: TxnType.ApplicationCall},
        ],
        {TxnField.fee: pt.Int(0)},
        pt.Seq(
            pt.InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.Payment}),
            pt.InnerTxnBuilder.Next(),
            pt.InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.AssetTransfer}),
            pt.InnerTxnBuilder.Next(),
            pt.InnerTxnBuilder.SetFields({TxnField.type_enum: TxnType.ApplicationCall}),
            pt.InnerTxnBuilder.Next(),
            pt.InnerTxnBuilder.SetFields(
                {
                    pt.TxnField.type_enum: TxnType.ApplicationCall,
                    pt.TxnField.application_id: pt.Int(1),
                    pt.TxnField.application_args: [
                        pt.MethodSignature("add(pay,txn,appl)void"),
                    ],
                    pt.TxnField.fee: pt.Int(0),
                }
            ),
        ),
    ),
)


@pytest.mark.parametrize("app_id, sig, args, fields, expectedExpr", ITXN_METHOD_CASES)
def test_InnerTxnBuilder_method_call(
    app_id: pt.Expr,
    sig: str,
    args: list[pt.abi.BaseType | pt.Expr | dict[pt.TxnField, pt.Expr | list[pt.Expr]]],
    fields: dict[pt.TxnField, pt.Expr | list[pt.Expr]],
    expectedExpr: pt.Expr,
):
    expr: pt.Expr = pt.InnerTxnBuilder.MethodCall(
        app_id=app_id, method_signature=sig, args=args, fields=fields
    )
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected, _ = expectedExpr.__teal__(teal6Options)
    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(teal6Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreScratchSlotEquality(), pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


# txn_test.py performs additional testing
