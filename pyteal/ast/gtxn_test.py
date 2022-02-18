import pytest

from .. import *

teal6Options = CompileOptions(version=6)


def test_gtxn_invalid():
    for f, e in [
        (lambda: Gtxn[-1], TealInputError),
        (lambda: Gtxn[MAX_GROUP_SIZE + 1], TealInputError),
        (lambda: Gtxn[Pop(Int(0))], TealTypeError),
        (lambda: Gtxn[Bytes("index")], TealTypeError),
    ]:
        with pytest.raises(e):
            f()


def test_gtxn_expr_invalid():
    for f, e in [
        (lambda: GtxnExpr(Assert(Int(1)), TxnField.sender), TealTypeError),
    ]:
        with pytest.raises(e):
            f()


def test_gtxn_expr_valid():
    [
        e.__teal__(teal6Options)
        for e in [
            GtxnExpr(1, TxnField.sender),
            GtxnExpr(Int(1), TxnField.sender),
        ]
    ]


def test_gtxna_expr_invalid():
    for f, e in [
        (lambda: GtxnaExpr("Invalid_type", TxnField.assets, 1), TealInputError),
        (lambda: GtxnaExpr(1, TxnField.assets, "Invalid_type"), TealInputError),
        (lambda: GtxnaExpr(Assert(Int(1)), TxnField.assets, 1), TealTypeError),
        (lambda: GtxnaExpr(1, TxnField.assets, Assert(Int(1))), TealTypeError),
    ]:
        with pytest.raises(e):
            f()


def test_gtxna_expr_valid():
    [
        e.__teal__(teal6Options)
        for e in [
            GtxnaExpr(1, TxnField.assets, 1),
            GtxnaExpr(Int(1), TxnField.assets, Int(1)),
        ]
    ]


# txn_test.py performs additional testing
