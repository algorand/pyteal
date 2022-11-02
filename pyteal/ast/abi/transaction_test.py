from dataclasses import dataclass
from typing import List, cast
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
    txn_type_enum: pt.Expr | None


TransactionValues: List[TransactionTypeTest] = [
    TransactionTypeTest(abi.TransactionTypeSpec(), abi.Transaction(), "txn", None),
    TransactionTypeTest(
        abi.KeyRegisterTransactionTypeSpec(),
        abi.KeyRegisterTransaction(),
        "keyreg",
        pt.TxnType.KeyRegistration,
    ),
    TransactionTypeTest(
        abi.PaymentTransactionTypeSpec(),
        abi.PaymentTransaction(),
        "pay",
        pt.TxnType.Payment,
    ),
    TransactionTypeTest(
        abi.AssetConfigTransactionTypeSpec(),
        abi.AssetConfigTransaction(),
        "acfg",
        pt.TxnType.AssetConfig,
    ),
    TransactionTypeTest(
        abi.AssetFreezeTransactionTypeSpec(),
        abi.AssetFreezeTransaction(),
        "afrz",
        pt.TxnType.AssetFreeze,
    ),
    TransactionTypeTest(
        abi.AssetTransferTransactionTypeSpec(),
        abi.AssetTransferTransaction(),
        "axfer",
        pt.TxnType.AssetTransfer,
    ),
    TransactionTypeTest(
        abi.ApplicationCallTransactionTypeSpec(),
        abi.ApplicationCallTransaction(),
        "appl",
        pt.TxnType.ApplicationCall,
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


def test_TransactionTypeSpec_txn_type_enum():
    for tv in TransactionValues:
        if tv.txn_type_enum is None:
            with pytest.raises(
                pt.TealInternalError,
                match=r"abi.TransactionTypeSpec does not represent a specific transaction type$",
            ):
                tv.ts.txn_type_enum()
        else:
            assert tv.ts.txn_type_enum() is tv.txn_type_enum


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


def test_Transaction__set_index():
    for tv in TransactionValues:
        val_to_set = 2
        expr = tv.t._set_index(val_to_set)

        assert expr.type_of() == pt.TealType.none
        assert expr.has_return() is False

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(expr, pt.Op.int, val_to_set),
                pt.TealOp(
                    None,
                    pt.Op.store,
                    cast(pt.ScratchVar, tv.t._stored_value).slot,
                ),
            ]
        )
        actual, _ = expr.__teal__(options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected
