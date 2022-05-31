import pyteal as pt
from pyteal import abi
import pytest

from pyteal.errors import TealInputError

options = pt.CompileOptions(version=5)


def test_Transaction_str():
    assert str(abi.TransactionTypeSpec()) == "txn"


def test_TransactionTypeSpec_is_dynamic():
    assert not (abi.TransactionTypeSpec()).is_dynamic()


def test_TransactionTypeSpec_new_instance():
    assert isinstance(abi.TransactionTypeSpec().new_instance(), abi.Account)


def test_TransactionTypeSpec_eq():
    assert abi.TransactionTypeSpec() == abi.Transaction.type_spec()

    for otherType in (
        abi.ByteTypeSpec(),
        abi.Uint8TypeSpec(),
        abi.AddressTypeSpec(),
    ):
        assert abi.TransactionTypeSpec() != otherType


def test_Transaction_encode():
    value = abi.Transaction()

    with pytest.raises(TealInputError):
        value.encode()


def test_Transaction_get():
    value = abi.Transaction()
    expr = value.get()
    pass


def test_Transaction_set():
    val_to_set = 2
    value = abi.Transaction()
    expr = value.set(val_to_set)
    pass