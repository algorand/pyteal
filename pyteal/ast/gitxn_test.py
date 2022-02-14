import pytest

from .. import *

teal5Options = CompileOptions(version=5)
teal6Options = CompileOptions(version=6)


def test_gitxn_invalid():
    with pytest.raises(TealInputError):
        GitxnExpr(0, TxnField.sender).__teal__(teal5Options)

    with pytest.raises(TealInputError):
        Gitxn[MAX_GROUP_SIZE].sender()

    with pytest.raises(TealInputError):
        Gitxn[-1].asset_sender()

    with pytest.raises(TealInputError):
        Gitxn[Bytes("first")].sender()


def test_gitxn_valid():
    for i in range(MAX_GROUP_SIZE):
        Gitxn[i].sender()


def test_gitxna_invalid():
    with pytest.raises(TealInputError):
        GitxnaExpr("Invalid_type", TxnField.application_args, 1).__teal__(teal6Options)

    with pytest.raises(TealInputError):
        GitxnaExpr(0, TxnField.application_args, "Invalid_type").__teal__(teal6Options)


def test_gitxna_valid():
    GitxnaExpr(0, TxnField.application_args, 1).__teal__(teal6Options)
    GitxnaExpr(0, TxnField.application_args, Assert(Int(1))).__teal__(teal6Options)


# txn_test.py performs additional testing
