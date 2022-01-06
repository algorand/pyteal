import pytest

from .. import *
from ..types import types_match

# this is not necessary but mypy complains if it's not included
from .. import MAX_GROUP_SIZE, CompileOptions

teal4Options = CompileOptions(version=4)
teal5Options = CompileOptions(version=5)
teal6Options = CompileOptions(version=6)


def test_InnerTxnBuilder_Begin():
    expr = InnerTxnBuilder.Begin()
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock([TealOp(expr, Op.itxn_begin)])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_InnerTxnBuilder_Submit():
    expr = InnerTxnBuilder.Submit()
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock([TealOp(expr, Op.itxn_submit)])

    actual, _ = expr.__teal__(teal5Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_InnerTxnBuilder_Next():
    expr = InnerTxnBuilder.Next()
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock([TealOp(expr, Op.itxn_next)])

    actual, _ = expr.__teal__(teal6Options)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal5Options)


def test_InnerTxnBuilder_SetField():
    for field in TxnField:
        if field.is_array:
            with pytest.raises(TealInputError):
                InnerTxnBuilder.SetField(field, Int(0))
            continue

        for value, opArgs in (
            (Int(0), (Op.int, 0)),
            (Bytes("value"), (Op.byte, '"value"')),
        ):
            assert field.type_of() in (TealType.uint64, TealType.bytes)

            if not types_match(field.type_of(), value.type_of()):
                with pytest.raises(TealTypeError):
                    InnerTxnBuilder.SetField(field, value)
                continue

            expr = InnerTxnBuilder.SetField(field, value)
            assert expr.type_of() == TealType.none
            assert not expr.has_return()

            expected = TealSimpleBlock(
                [TealOp(value, *opArgs), TealOp(expr, Op.itxn_field, field.arg_name)]
            )

            actual, _ = expr.__teal__(teal5Options)
            actual.addIncoming()
            actual = TealBlock.NormalizeBlocks(actual)

            assert actual == expected

            with pytest.raises(TealInputError):
                expr.__teal__(teal4Options)


def test_InnerTxnBuilder_SetFields():
    cases = (
        ({}, Seq()),
        ({TxnField.amount: Int(5)}, InnerTxnBuilder.SetField(TxnField.amount, Int(5))),
        (
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.close_remainder_to: Txn.sender(),
            },
            Seq(
                InnerTxnBuilder.SetField(TxnField.type_enum, TxnType.Payment),
                InnerTxnBuilder.SetField(TxnField.close_remainder_to, Txn.sender()),
            ),
        ),
    )

    for fields, expectedExpr in cases:
        expr = InnerTxnBuilder.SetFields(fields)
        assert expr.type_of() == TealType.none
        assert not expr.has_return()

        expected, _ = expectedExpr.__teal__(teal5Options)
        expected.addIncoming()
        expected = TealBlock.NormalizeBlocks(expected)

        actual, _ = expr.__teal__(teal5Options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        with TealComponent.Context.ignoreExprEquality():
            assert actual == expected

        if len(fields) != 0:
            with pytest.raises(TealInputError):
                expr.__teal__(teal4Options)


# txn_test.py performs additional testing
