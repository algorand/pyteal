import pyteal as pt
from pyteal import abi
import pytest

from pyteal.errors import TealInputError

options = pt.CompileOptions(version=5)


def test_AnyTransaction_str():
    assert str(abi.AnyTransactionTypeSpec()) == "txn"


def test_AnyTransactionTypeSpec_is_dynamic():
    assert not (abi.AnyTransactionTypeSpec()).is_dynamic()


def test_AnyTransactionTypeSpec_new_instance():
    assert isinstance(abi.AnyTransactionTypeSpec().new_instance(), abi.AnyTransaction)


def test_AnyTransactionTypeSpec_eq():
    assert abi.AnyTransactionTypeSpec() == abi.AnyTransactionTypeSpec()

    for otherType in (
        abi.ByteTypeSpec(),
        abi.Uint8TypeSpec(),
        abi.AddressTypeSpec(),
    ):
        assert abi.AnyTransactionTypeSpec() != otherType


def test_AnyTransaction_encode():
    value = abi.AnyTransaction()
    with pytest.raises(TealInputError):
        value.encode()


# def test_AnyTransaction_get():
#    value = abi.AnyTransaction()
#    with pytest.raises(TealInputError):
#        value.get()
#
# def test_Transaction_set():
#    val_to_set = 2
#    value = abi.Transaction()
#    expr = value.set(val_to_set)
#    pass
