import pyteal as pt
from pyteal import abi
import pytest
from pyteal.ast.txn import TxnObject

from pyteal.errors import TealInputError

options = pt.CompileOptions(version=5)


def test_Transaction_str():
    assert str(abi.TransactionTypeSpec()) == "txn"


def test_TransactionTypeSpec_is_dynamic():
    assert not (abi.TransactionTypeSpec()).is_dynamic()


def test_TransactionTypeSpec_new_instance():
    assert isinstance(abi.TransactionTypeSpec().new_instance(), abi.Transaction)


def test_TransactionTypeSpec_eq():
    assert abi.TransactionTypeSpec() == abi.TransactionTypeSpec()

    for otherType in (
        abi.ByteTypeSpec(),
        abi.Uint8TypeSpec(),
        abi.AddressTypeSpec(),
    ):
        assert abi.TransactionTypeSpec() != otherType


def test_Transaction_typespec():
    assert abi.Transaction().type_spec() == abi.TransactionTypeSpec()


def test_Transaction_decode():
    value = abi.Transaction()
    with pytest.raises(TealInputError):
        value.decode("")


def test_Transaction_encode():
    value = abi.Transaction()
    with pytest.raises(TealInputError):
        value.encode()


def test_Transaction_get():
    value = abi.Transaction()
    expr = value.get()
    assert isinstance(expr, pt.TxnObject)


def test_Transaction_set():
    val_to_set = 2
    value = abi.Transaction()
    expr = value.set(val_to_set)

    assert expr.type_of() == pt.TealType.none
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, pt.Op.int, val_to_set),
            pt.TealOp(None, pt.Op.store, value.stored_value.slot),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected
