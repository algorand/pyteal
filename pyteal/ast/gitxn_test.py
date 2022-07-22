import pytest

import pyteal as pt

avm5Options = pt.CompileOptions(version=5)
avm6Options = pt.CompileOptions(version=6)


def test_gitxn_invalid():
    for ctor, e in [
        (
            lambda: pt.Gitxn[pt.MAX_GROUP_SIZE],
            pt.TealInputError,
        ),
        (
            lambda: pt.Gitxn[-1],
            pt.TealInputError,
        ),
    ]:
        with pytest.raises(e):
            ctor()


def test_gitxn_valid():
    for i in range(pt.MAX_GROUP_SIZE):
        pt.Gitxn[i].sender()


def test_gitxn_expr_invalid():
    for f, e in [
        (
            lambda: pt.GitxnExpr(pt.Int(1), pt.TxnField.sender),
            pt.TealInputError,
        ),
        (
            lambda: pt.GitxnExpr(1, pt.TxnField.sender).__teal__(avm5Options),
            pt.TealInputError,
        ),
    ]:
        with pytest.raises(e):
            f()


def test_gitxn_expr_valid():
    pt.GitxnExpr(1, pt.TxnField.sender).__teal__(avm6Options)


def test_gitxna_expr_invalid():
    for f, e in [
        (
            lambda: pt.GitxnaExpr("Invalid_type", pt.TxnField.application_args, 1),
            pt.TealInputError,
        ),
        (
            lambda: pt.GitxnaExpr(1, pt.TxnField.application_args, "Invalid_type"),
            pt.TealInputError,
        ),
        (
            lambda: pt.GitxnaExpr(
                0, pt.TxnField.application_args, pt.Assert(pt.Int(1))
            ),
            pt.TealTypeError,
        ),
        (
            lambda: pt.GitxnaExpr(0, pt.TxnField.application_args, 0).__teal__(
                avm5Options
            ),
            pt.TealInputError,
        ),
    ]:
        with pytest.raises(e):
            f()


def test_gitxna_valid():
    [
        e.__teal__(avm6Options)
        for e in [
            pt.GitxnaExpr(0, pt.TxnField.application_args, 1),
            pt.GitxnaExpr(0, pt.TxnField.application_args, pt.Int(1)),
        ]
    ]


# txn_test.py performs additional testing
