import pytest

import pyteal as pt

avm6Options = pt.CompileOptions(version=6)


def test_gtxn_invalid():
    for f, e in [
        (lambda: pt.Gtxn[-1], pt.TealInputError),
        (lambda: pt.Gtxn[pt.MAX_GROUP_SIZE + 1], pt.TealInputError),
        (lambda: pt.Gtxn[pt.Pop(pt.Int(0))], pt.TealTypeError),
        (lambda: pt.Gtxn[pt.Bytes("index")], pt.TealTypeError),
    ]:
        with pytest.raises(e):
            f()


def test_gtxn_expr_invalid():
    for f, e in [
        (
            lambda: pt.GtxnExpr(pt.Assert(pt.Int(1)), pt.TxnField.sender),
            pt.TealTypeError,
        ),
    ]:
        with pytest.raises(e):
            f()


def test_gtxn_expr_valid():
    [
        e.__teal__(avm6Options)
        for e in [
            pt.GtxnExpr(1, pt.TxnField.sender),
            pt.GtxnExpr(pt.Int(1), pt.TxnField.sender),
        ]
    ]


def test_gtxna_expr_invalid():
    for f, e in [
        (
            lambda: pt.GtxnaExpr("Invalid_type", pt.TxnField.assets, 1),
            pt.TealInputError,
        ),
        (
            lambda: pt.GtxnaExpr(1, pt.TxnField.assets, "Invalid_type"),
            pt.TealInputError,
        ),
        (
            lambda: pt.GtxnaExpr(pt.Assert(pt.Int(1)), pt.TxnField.assets, 1),
            pt.TealTypeError,
        ),
        (
            lambda: pt.GtxnaExpr(1, pt.TxnField.assets, pt.Assert(pt.Int(1))),
            pt.TealTypeError,
        ),
    ]:
        with pytest.raises(e):
            f()


def test_gtxna_expr_valid():
    [
        e.__teal__(avm6Options)
        for e in [
            pt.GtxnaExpr(1, pt.TxnField.assets, 1),
            pt.GtxnaExpr(pt.Int(1), pt.TxnField.assets, pt.Int(1)),
        ]
    ]


# txn_test.py performs additional testing
