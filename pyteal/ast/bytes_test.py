import pytest

from .. import *

def test_bytes_base32_no_padding():
    for s in ("ME", "MFRA", "MFRGG", "MFRGGZA", "MFRGGZDF", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M"):
        expr = Bytes("base32", s)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.byte, "base32(" + s + ")")
        ]

def test_bytes_base32_padding():
    for s in ("ME======", "MFRA====", "MFRGG===", "MFRGGZA=", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M======"):
        expr = Bytes("base32", s)
        assert expr.type_of() == TealType.bytes
        assert expr.__teal__() == [
            TealOp(Op.byte, "base32(" + s + ")")
        ]

def test_bytes_base32_empty():
    expr = Bytes("base32", "")
    assert expr.__teal__() == [
        TealOp(Op.byte, "base32()")
    ]

def test_bytes_base64():
    expr = Bytes("base64", "Zm9vYmE=")
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.byte, "base64(Zm9vYmE=)")
    ]

def test_bytes_base64_empty():
    expr = Bytes("base64", "")
    assert expr.__teal__() == [
        TealOp(Op.byte, "base64()")
    ]

def test_bytes_base16():
    expr = Bytes("base16", "A21212EF")
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.byte, "0xA21212EF")
    ]

def test_bytes_base16_prefix():
    expr = Bytes("base16", "0xA21212EF")
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.byte, "0xA21212EF")
    ]

def test_bytes_base16_empty():
    expr = Bytes("base16", "")
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.byte, "0x")
    ]

def test_bytes_utf8():
    expr = Bytes("hello world")
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.byte, "\"hello world\"")
    ]

def test_bytes_utf8_special_chars():
    expr = Bytes("\t \n \r\n \\ \" \' 😀")
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.byte, "\"\\t \\n \\r\\n \\\\ \\\" \' \\xf0\\x9f\\x98\\x80\"")
    ]

def test_bytes_utf8_empty():
    expr = Bytes("")
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.byte, "\"\"")
    ]

def test_bytes_invalid():
    with pytest.raises(TealInputError):
        Bytes("base23", "")

    with pytest.raises(TealInputError):
        Bytes("base32", "Zm9vYmE=")

    with pytest.raises(TealInputError):
        Bytes("base32", "MFRGG====")

    with pytest.raises(TealInputError):
        Bytes("base32", "MFRGG==")

    with pytest.raises(TealInputError):
        Bytes("base32", "CCCCCC==")

    with pytest.raises(TealInputError):
        Bytes("base32", "CCCCCC")

    with pytest.raises(TealInputError):
        Bytes("base32", "C=======")
            
    with pytest.raises(TealInputError):
        Bytes("base32", "C")
    
    with pytest.raises(TealInputError):
        Bytes("base32", "=")

    with pytest.raises(TealInputError):
        Bytes("base64", "?????")

    with pytest.raises(TealInputError):
        Bytes("base16", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
