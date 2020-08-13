import pytest

from .. import *

def test_nonce_base32():
    expr = Nonce("base32", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M", Int(1))
    assert expr.__teal__() == [
        ["byte", "base32(7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M)"],
        ["pop"],
        ["int", "1"]
    ]

def test_nonce_base32_empty():
    expr = Nonce("base32", "", Int(1))
    assert expr.__teal__() == [
        ["byte", "base32()"],
        ["pop"],
        ["int", "1"]
    ]

def test_nonce_base64():
    expr = Nonce("base64", "Zm9vYmE=", Int(1))
    assert expr.__teal__() == [
        ["byte", "base64(Zm9vYmE=)"],
        ["pop"],
        ["int", "1"]
    ]

def test_nonce_base64_empty():
    expr = Nonce("base64", "", Int(1))
    assert expr.__teal__() == [
        ["byte", "base64()"],
        ["pop"],
        ["int", "1"]
    ]

def test_nonce_base16():
    expr = Nonce("base16", "A21212EF", Int(1))
    assert expr.__teal__() == [
        ["byte", "0xA21212EF"],
        ["pop"],
        ["int", "1"]
    ]

def test_nonce_base16_prefix():
    expr = Nonce("base16", "0xA21212EF", Int(1))
    assert expr.__teal__() == [
        ["byte", "0xA21212EF"],
        ["pop"],
        ["int", "1"]
    ]

def test_nonce_base16_empty():
    expr = Nonce("base16", "", Int(1))
    assert expr.__teal__() == [
        ["byte", "0x"],
        ["pop"],
        ["int", "1"]
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
