import pytest

import pyteal as pt
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


# txn_test.py performs additional testing
