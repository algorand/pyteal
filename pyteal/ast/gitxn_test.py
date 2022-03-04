import pytest

from .. import *

teal5Options = CompileOptions(version=5)
teal6Options = CompileOptions(version=6)


def test_gitxn_invalid():
    for ctor, e in [
        (
            lambda: Gitxn[MAX_GROUP_SIZE],
            TealInputError,
        ),
        (
            lambda: Gitxn[-1],
            TealInputError,
        ),
    ]:
        with pytest.raises(e):
            ctor()


def test_gitxn_valid():
    for i in range(MAX_GROUP_SIZE):
        Gitxn[i].sender()


def test_gitxn_expr_invalid():
    for f, e in [
        (
            lambda: GitxnExpr(Int(1), TxnField.sender),
            TealInputError,
        ),
        (
            lambda: GitxnExpr(1, TxnField.sender).__teal__(teal5Options),
            TealInputError,
        ),
    ]:
        with pytest.raises(e):
            f()


def test_gitxn_expr_valid():
    GitxnExpr(1, TxnField.sender).__teal__(teal6Options)


def test_gitxna_expr_invalid():
    for f, e in [
        (
            lambda: GitxnaExpr("Invalid_type", TxnField.application_args, 1),
            TealInputError,
        ),
        (
            lambda: GitxnaExpr(1, TxnField.application_args, "Invalid_type"),
            TealInputError,
        ),
        (
            lambda: GitxnaExpr(0, TxnField.application_args, Assert(Int(1))),
            TealTypeError,
        ),
        (
            lambda: GitxnaExpr(0, TxnField.application_args, 0).__teal__(teal5Options),
            TealInputError,
        ),
    ]:
        with pytest.raises(e):
            f()


def test_gitxna_valid():
    [
        e.__teal__(teal6Options)
        for e in [
            GitxnaExpr(0, TxnField.application_args, 1),
            GitxnaExpr(0, TxnField.application_args, Int(1)),
        ]
    ]


# txn_test.py performs additional testing
