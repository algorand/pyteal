import pytest

import pyteal as pt
from pyteal import abi
from pyteal.ast.abi.util import substringForDecoding
from pyteal.ast.abi.type_test import ContainerType
from pyteal.util import escapeStr

options = pt.CompileOptions(version=5)


def test_Account_str():
    assert str(abi.AccountTypeSpec()) == "account"


def test_AccountTypeSpec_is_dynamic():
    assert not (abi.AccountTypeSpec()).is_dynamic()


def test_AccountTypeSpec_new_instance():
    assert isinstance(abi.AccountTypeSpec().new_instance(), abi.Account)


def test_AccountTypeSpec_eq():
    assert abi.AccountTypeSpec() == abi.AccountTypeSpec()

    for otherType in (
        abi.ByteTypeSpec(),
        abi.Uint8TypeSpec(),
        abi.AddressTypeSpec(),
    ):
        assert abi.StringTypeSpec() != otherType


# def test_Account_encode():
#    value = abi.Account()
#    expr = value.encode()
#    assert expr.type_of() == pt.TealType.bytes
#    assert expr.has_return() is False
#
#    expected = pt.TealSimpleBlock(
#        [
#            pt.TealOp(expr, pt.Op.byte, "0x00"),
#            pt.TealOp(None, pt.Op.int, 0),
#            pt.TealOp(None, pt.Op.load, value.stored_value.slot),
#            pt.TealOp(None, pt.Op.setbyte)
#        ]
#    )
#    actual, _ = expr.__teal__(options)
#    actual.addIncoming()
#    assert actual == expected


def test_Account_get():
    value = abi.Account()
    expr = value.get()
    assert expr.type_of() == pt.TealType.bytes
    assert expr.has_return() is False

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, pt.Op.load, value.stored_value.slot),
            pt.TealOp(None, pt.Op.txnas, "Accounts"),
        ]
    )
    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected
