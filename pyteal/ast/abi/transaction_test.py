from dataclasses import dataclass
from typing import List
import pyteal as pt
from pyteal import abi
import pytest

from pyteal.errors import TealInputError

options = pt.CompileOptions(version=5)


@dataclass
class TransactionTypeTest:
    ts: abi.TransactionTypeSpec
    t: abi.Transaction
    s: str


TransactionValues: List[TransactionTypeTest] = [
    TransactionTypeTest(abi.TransactionTypeSpec(), abi.Transaction(), "txn"),
    TransactionTypeTest(
        abi.KeyRegisterTransactionTypeSpec(), abi.KeyRegisterTransaction(), "keyreg"
    ),
    TransactionTypeTest(
        abi.PaymentTransactionTypeSpec(), abi.PaymentTransaction(), "pay"
    ),
    TransactionTypeTest(
        abi.AssetConfigTransactionTypeSpec(), abi.AssetConfigTransaction(), "acfg"
    ),
    TransactionTypeTest(
        abi.AssetFreezeTransactionTypeSpec(), abi.AssetFreezeTransaction(), "afrz"
    ),
    TransactionTypeTest(
        abi.AssetTransferTransactionTypeSpec(), abi.AssetTransferTransaction(), "axfer"
    ),
    TransactionTypeTest(
        abi.ApplicationCallTransactionTypeSpec(),
        abi.ApplicationCallTransaction(),
        "appl",
    ),
]


def test_Transaction_str():
    for tv in TransactionValues:
        assert str(tv.ts) == tv.s


def test_TransactionTypeSpec_is_dynamic():
    for tv in TransactionValues:
        assert not (tv.ts).is_dynamic()


def test_TransactionTypeSpec_new_instance():
    for tv in TransactionValues:
        assert isinstance(tv.ts.new_instance(), abi.Transaction)


def test_TransactionTypeSpec_eq():
    for tv in TransactionValues:
        assert tv.ts == tv.ts

        for otherType in (
            abi.ByteTypeSpec(),
            abi.Uint8TypeSpec(),
            abi.AddressTypeSpec(),
        ):
            assert tv.ts != otherType


def test_Transaction_typespec():
    for tv in TransactionValues:
        assert tv.t.type_spec() == tv.ts


def test_Transaction_decode():
    for tv in TransactionValues:
        with pytest.raises(TealInputError):
            tv.t.decode("")


def test_Transaction_encode():
    for tv in TransactionValues:
        with pytest.raises(TealInputError):
            tv.t.encode()


def test_Transaction_get():
    for tv in TransactionValues:
        expr = tv.t.get()
        assert isinstance(expr, pt.TxnObject)


def test_Transaction_set():
    for tv in TransactionValues:
        val_to_set = 2
        expr = tv.t.set(val_to_set)

        assert expr.type_of() == pt.TealType.none
        assert expr.has_return() is False

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(expr, pt.Op.int, val_to_set),
                pt.TealOp(None, pt.Op.store, tv.t.stored_value.slot),
            ]
        )
        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected
