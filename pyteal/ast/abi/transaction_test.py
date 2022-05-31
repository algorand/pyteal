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


def test_AnyTransaction_typespec():
    assert abi.AnyTransaction().type_spec() == abi.AnyTransactionTypeSpec()


def test_AnyTransaction_decode():
    value = abi.AnyTransaction()
    with pytest.raises(TealInputError):
        value.decode("")


def test_AnyTransaction_encode():
    value = abi.AnyTransaction()
    with pytest.raises(TealInputError):
        value.encode()


def test_AnyTransaction_get():
    value = abi.AnyTransaction()
    expr = value.get()
    assert expr.type_of() == pt.TealType.uint64
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, pt.Op.load, value.stored_value.slot),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_AnyTransaction_set():
    val_to_set = 2
    value = abi.AnyTransaction()
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
