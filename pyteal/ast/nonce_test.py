import pytest

from .. import *

def test_nonce_base32():
    expr = Nonce("base32", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M", Int(1))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.byte, "base32(7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M)"),
        TealOp(Op.pop),
        TealOp(Op.int, 1)
    ]

def test_nonce_base32_empty():
    expr = Nonce("base32", "", Int(1))
    assert expr.__teal__() == [
        TealOp(Op.byte, "base32()"),
        TealOp(Op.pop),
        TealOp(Op.int, 1)
    ]

def test_nonce_base64():
    expr = Nonce("base64", "Zm9vYmE=", Txn.sender())
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.byte, "base64(Zm9vYmE=)"),
        TealOp(Op.pop),
        TealOp(Op.txn, "Sender")
    ]

def test_nonce_base64_empty():
    expr = Nonce("base64", "", Int(1))
    assert expr.__teal__() == [
        TealOp(Op.byte, "base64()"),
        TealOp(Op.pop),
        TealOp(Op.int, 1)
    ]

def test_nonce_base16():
    expr = Nonce("base16", "A21212EF", Int(1))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.byte, "0xA21212EF"),
        TealOp(Op.pop),
        TealOp(Op.int, 1)
    ]

def test_nonce_base16_prefix():
    expr = Nonce("base16", "0xA21212EF", Int(1))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.byte, "0xA21212EF"),
        TealOp(Op.pop),
        TealOp(Op.int, 1)
    ]

def test_nonce_base16_empty():
    expr = Nonce("base16", "", Int(6))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.byte, "0x"),
        TealOp(Op.pop),
        TealOp(Op.int, 6)
    ]

def test_nonce_invalid():
    with pytest.raises(TealInputError):
        Nonce("base23", "", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base32", "Zm9vYmE=", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base64", "?????", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base16", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M", Int(1))
