import pytest

import pyteal as pt
from pyteal.ast.txn import Txn, TxnField, TxnType
from pyteal.types import types_match

avm4Options = pt.CompileOptions(version=4)
avm5Options = pt.CompileOptions(version=5)
avm6Options = pt.CompileOptions(version=6)


def test_InnerTxnBuilder_Begin():
    expr = pt.InnerTxnBuilder.Begin()
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.itxn_begin)])

    actual, _ = expr.__teal__(avm5Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm4Options)


def test_InnerTxnBuilder_Submit():
    expr = pt.InnerTxnBuilder.Submit()
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.itxn_submit)])

    actual, _ = expr.__teal__(avm5Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm4Options)


def test_InnerTxnBuilder_Next():
    expr = pt.InnerTxnBuilder.Next()
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.itxn_next)])

    actual, _ = expr.__teal__(avm6Options)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm5Options)


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

            actual, _ = expr.__teal__(avm5Options)
            actual.addIncoming()
            actual = pt.TealBlock.NormalizeBlocks(actual)

            assert actual == expected

            with pytest.raises(pt.TealInputError):
                expr.__teal__(avm4Options)


ITXN_FIELDS_CASES = [
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
    (
        {pt.TxnField.accounts: pt.Txn.accounts},
        pt.For(
            (i := pt.ScratchVar()).store(pt.Int(0)),
            i.load() < pt.Txn.accounts.length(),
            i.store(i.load() + pt.Int(1)),
        ).Do(
            pt.InnerTxnBuilder.SetField(pt.TxnField.accounts, [Txn.accounts[i.load()]])
        ),
    ),
]


def test_InnerTxnBuilder_SetFields():
    for fields, expectedExpr in ITXN_FIELDS_CASES:
        expr = pt.InnerTxnBuilder.SetFields(fields)
        assert expr.type_of() == pt.TealType.none
        assert not expr.has_return()

        expected, _ = expectedExpr.__teal__(avm5Options)
        expected.addIncoming()
        expected = pt.TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(avm5Options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreScratchSlotEquality(), pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected

        assert pt.TealBlock.MatchScratchSlotReferences(
            pt.TealBlock.GetReferencedScratchSlots(actual),
            pt.TealBlock.GetReferencedScratchSlots(expected),
        )

        if len(fields) != 0:
            with pytest.raises(pt.TealInputError):
                expr.__teal__(avm4Options)


def test_InnerTxnBuilder_Execute():
    for fields, expectedExpr in ITXN_FIELDS_CASES:
        expr = pt.InnerTxnBuilder.Execute(fields)

        expected, _ = pt.Seq(
            pt.InnerTxnBuilder.Begin(),
            expectedExpr,
            pt.InnerTxnBuilder.Submit(),
        ).__teal__(avm5Options)
        expected.addIncoming()
        expected = pt.TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(avm5Options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreScratchSlotEquality(), pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected

        assert pt.TealBlock.MatchScratchSlotReferences(
            pt.TealBlock.GetReferencedScratchSlots(actual),
            pt.TealBlock.GetReferencedScratchSlots(expected),
        )

        with pytest.raises(pt.TealInputError):
            expr.__teal__(avm4Options)


ITXN_METHOD_CASES = (
    (
        pt.Int(1),
        "add(uint64,uint64)void",
        [t1_1 := pt.Itob(pt.Int(1)), t1_2 := pt.Itob(pt.Int(1))],
        {TxnField.fee: pt.Int(0)},
        pt.Seq(
            pt.InnerTxnBuilder.SetFields(
                {
                    pt.TxnField.type_enum: TxnType.ApplicationCall,
                    pt.TxnField.application_id: pt.Int(1),
                    pt.TxnField.application_args: [
                        pt.MethodSignature("add(uint64,uint64)void"),
                        t1_1,
                        t1_2,
                    ],
                    pt.TxnField.fee: pt.Int(0),
                }
            ),
        ),
        None,
    ),
    (
        pt.Int(1),
        "add(uint64,uint64)void",
        [t2_1 := pt.abi.Uint64(), t2_2 := pt.abi.Uint64()],
        {TxnField.fee: pt.Int(0)},
        pt.Seq(
            pt.InnerTxnBuilder.SetFields(
                {
                    pt.TxnField.type_enum: TxnType.ApplicationCall,
                    pt.TxnField.application_id: pt.Int(1),
                    pt.TxnField.application_args: [
                        pt.MethodSignature("add(uint64,uint64)void"),
                        t2_1.encode(),
                        t2_2.encode(),
                    ],
                    pt.TxnField.fee: pt.Int(0),
                }
            ),
        ),
        None,
    ),
    (
        pt.Int(1),
        "add(application,account,asset)void",
        [
            t3_1 := pt.abi.Application(),
            t3_2 := pt.abi.Account(),
            t3_3 := pt.abi.Asset(),
        ],
        {TxnField.fee: pt.Int(0)},
        pt.Seq(
            pt.InnerTxnBuilder.SetFields(
                {
                    pt.TxnField.type_enum: TxnType.ApplicationCall,
                    pt.TxnField.application_id: pt.Int(1),
                    pt.TxnField.accounts: [t3_2.address()],
                    pt.TxnField.applications: [t3_1.application_id()],
                    pt.TxnField.assets: [t3_3.asset_id()],
                    pt.TxnField.application_args: [
                        pt.MethodSignature("add(application,account,asset)void"),
                        pt.Bytes(b"\x01"),
                        pt.Bytes(b"\x01"),
                        pt.Bytes(b"\x00"),
                    ],
                    pt.TxnField.fee: pt.Int(0),
                }
            ),
        ),
        None,
    ),
    (
        pt.Int(1),
        "add(application,account,asset)void",
        [
            t4_1 := pt.Int(1),
            t4_2 := pt.Global.zero_address(),
            t4_3 := pt.Int(2),
        ],
        {TxnField.fee: pt.Int(0)},
        pt.Seq(
            pt.InnerTxnBuilder.SetFields(
                {
                    pt.TxnField.type_enum: TxnType.ApplicationCall,
                    pt.TxnField.application_id: pt.Int(1),
                    pt.TxnField.accounts: [t4_2],
                    pt.TxnField.applications: [t4_1],
                    pt.TxnField.assets: [t4_3],
                    pt.TxnField.application_args: [
                        pt.MethodSignature("add(application,account,asset)void"),
                        pt.Bytes(b"\x01"),
                        pt.Bytes(b"\x01"),
                        pt.Bytes(b"\x00"),
                    ],
                    pt.TxnField.fee: pt.Int(0),
                }
            ),
        ),
        None,
    ),
    (
        pt.Int(1),
        "add(pay,txn,appl)void",
        [
            t5_1 := {TxnField.type_enum: TxnType.Payment},
            t5_2 := {TxnField.type_enum: TxnType.AssetTransfer},
            t5_3 := {TxnField.type_enum: TxnType.ApplicationCall},
        ],
        {TxnField.fee: pt.Int(0)},
        pt.Seq(
            pt.InnerTxnBuilder.SetFields(t5_1),  # type: ignore
            pt.InnerTxnBuilder.Next(),
            pt.InnerTxnBuilder.SetFields(t5_2),  # type: ignore
            pt.InnerTxnBuilder.Next(),
            pt.InnerTxnBuilder.SetFields(t5_3),  # type: ignore
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
        None,
    ),
    (
        pt.Int(1),
        "query(byte[],uint64)void",
        [t6_1 := pt.abi.DynamicBytes(), t6_2 := pt.abi.Uint64()],
        {TxnField.fee: pt.Int(0)},
        pt.Seq(
            pt.InnerTxnBuilder.SetFields(
                {
                    pt.TxnField.type_enum: TxnType.ApplicationCall,
                    pt.TxnField.application_id: pt.Int(1),
                    pt.TxnField.application_args: [
                        pt.MethodSignature("query(byte[],uint64)void"),
                        t6_1.encode(),
                        t6_2.encode(),
                    ],
                    pt.TxnField.fee: pt.Int(0),
                }
            ),
        ),
        None,
    ),
    # Error cases
    (
        pt.Int(1),
        "add(pay,txn,appl)void",
        [
            {},
            {TxnField.type_enum: TxnType.AssetTransfer},
            {TxnField.type_enum: TxnType.ApplicationCall},
        ],
        None,
        None,
        pt.TealInputError,
    ),
    (
        pt.Int(1),
        "add(pay,txn,appl)void",
        [
            {TxnField.type_enum: pt.Int(10)},
            {TxnField.type_enum: TxnType.AssetTransfer},
            {TxnField.type_enum: TxnType.ApplicationCall},
        ],
        None,
        None,
        pt.TealTypeError,
    ),
    (
        pt.Int(1),
        "add(pay,txn,appl)void",
        [
            {TxnField.type_enum: TxnType.ApplicationCall},
            {TxnField.type_enum: TxnType.AssetTransfer},
            {TxnField.type_enum: TxnType.ApplicationCall},
        ],
        None,
        None,
        pt.TealInputError,
    ),
    (
        pt.Int(1),
        "add(application,account,asset)void",
        [
            pt.abi.Asset(),
            pt.abi.Account(),
            pt.abi.Asset(),
        ],
        None,
        None,
        pt.TealTypeError,
    ),
    (
        pt.Int(1),
        "add(application)void",
        [
            pt.Bytes(""),
        ],
        None,
        None,
        pt.TealTypeError,
    ),
    (
        pt.Int(1),
        "add(asset)void",
        [
            pt.Bytes(""),
        ],
        None,
        None,
        pt.TealTypeError,
    ),
    (
        pt.Int(1),
        "add(account)void",
        [
            pt.Int(1),
        ],
        None,
        None,
        pt.TealTypeError,
    ),
    (
        pt.Int(1),
        "add(uint64,uint64)void",
        [pt.abi.String(), pt.abi.Uint64()],
        None,
        None,
        pt.TealTypeError,
    ),
    (
        pt.Int(1),
        "add(uint64,uint64)void",
        [pt.abi.Uint64()],
        None,
        None,
        pt.TealInputError,
    ),
    (
        pt.Int(1),
        "add(uint64,uint64)void",
        [pt.abi.Uint64(), pt.abi.Uint64(), pt.abi.Uint64()],
        None,
        None,
        pt.TealInputError,
    ),
)


@pytest.mark.parametrize(
    "app_id, sig, args, extra_fields, expected_expr, expected_error", ITXN_METHOD_CASES
)
def test_InnerTxnBuilder_method_call(
    app_id: pt.Expr,
    sig: str,
    args: list[pt.abi.BaseType | pt.Expr | dict[pt.TxnField, pt.Expr | list[pt.Expr]]],
    extra_fields: dict[pt.TxnField, pt.Expr | list[pt.Expr]],
    expected_expr: pt.Expr,
    expected_error: type[Exception],
):

    if expected_error is not None:
        with pytest.raises(expected_error):
            pt.InnerTxnBuilder.MethodCall(
                app_id=app_id,
                method_signature=sig,
                args=args,
                extra_fields=extra_fields,
            )
        with pytest.raises(expected_error):
            pt.InnerTxnBuilder.ExecuteMethodCall(
                app_id=app_id,
                method_signature=sig,
                args=args,
                extra_fields=extra_fields,
            )
        return

    # First run the test with MethodCall
    expr: pt.Expr = pt.InnerTxnBuilder.MethodCall(
        app_id=app_id, method_signature=sig, args=args, extra_fields=extra_fields
    )
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected, _ = expected_expr.__teal__(avm6Options)
    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(avm6Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreScratchSlotEquality(), pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected
        assert pt.TealBlock.MatchScratchSlotReferences(
            pt.TealBlock.GetReferencedScratchSlots(actual),
            pt.TealBlock.GetReferencedScratchSlots(expected),
        )

    # Now run the same test with ExecuteMethodCall
    expr = pt.InnerTxnBuilder.ExecuteMethodCall(
        app_id=app_id, method_signature=sig, args=args, extra_fields=extra_fields
    )
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected, _ = pt.Seq(
        pt.InnerTxnBuilder.Begin(), expected_expr, pt.InnerTxnBuilder.Submit()
    ).__teal__(avm6Options)
    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(avm6Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreScratchSlotEquality(), pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected
        assert pt.TealBlock.MatchScratchSlotReferences(
            pt.TealBlock.GetReferencedScratchSlots(actual),
            pt.TealBlock.GetReferencedScratchSlots(expected),
        )


# txn_test.py performs additional testing
