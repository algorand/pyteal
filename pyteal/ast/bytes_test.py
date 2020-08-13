import pytest

from .. import *

def test_bytes_base32():
    expr = Bytes("base32", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
    assert expr.__teal__() == [
        ["byte", "base32(7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M)"]
    ]

def test_bytes_base32_empty():
    expr = Bytes("base32", "")
    assert expr.__teal__() == [
        ["byte", "base32()"]
    ]

def test_bytes_base64():
    expr = Bytes("base64", "Zm9vYmE=")
    assert expr.__teal__() == [
        ["byte", "base64(Zm9vYmE=)"]
    ]

def test_bytes_base64_empty():
    expr = Bytes("base64", "")
    assert expr.__teal__() == [
        ["byte", "base64()"]
    ]

def test_bytes_base16():
    expr = Bytes("base16", "A21212EF")
    assert expr.__teal__() == [
        ["byte", "0xA21212EF"]
    ]

def test_bytes_base16_prefix():
    b16_2 = Bytes("base16", "0xA21212EF")
    assert b16_2.__teal__() == [
        ["byte", "0xA21212EF"]
    ]

def test_bytes_base16_empty():
    expr = Bytes("base16", "")
    assert expr.__teal__() == [
        ["byte", "0x"]
    ]

def test_bytes_invalid():
    with pytest.raises(TealInputError):
        Bytes("base23", "")

    with pytest.raises(TealInputError):
        Bytes("base32", "Zm9vYmE=")

    with pytest.raises(TealInputError):
        Bytes("base64", "?????")

    with pytest.raises(TealInputError):
        Bytes("base16", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
