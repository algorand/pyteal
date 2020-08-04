import pytest

from .. import *

def test_btoi():
    expr = Btoi(Arg(1))
    assert expr.__teal__() == [
        ["arg", "1"],
        ["btoi"]
    ]

def test_btoi_invalid():
    with pytest.raises(TealTypeError):
        Btoi(Int(1))

def test_itob():
    expr = Itob(Int(1))
    assert expr.__teal__() == [
        ["int", "1"],
        ["itob"]
    ]

def test_itob_invalid():
    with pytest.raises(TealTypeError):
        Itob(Arg(1))

def test_len():
    expr = Len(Txn.receiver())
    assert expr.__teal__() == [
        ["txn", "Receiver"],
        ["len"]
    ]

def test_len_invalid():
    with pytest.raises(TealTypeError):
        Len(Int(1))

def test_sha256():
    expr = Sha256(Arg(0))
    assert expr.__teal__() == [
        ["arg", "0"],
        ["sha256"]
    ]

def test_sha256_invalid():
    with pytest.raises(TealTypeError):
        Sha256(Int(1))

def test_sha512_256():
    expr = Sha512_256(Arg(0))
    assert expr.__teal__() == [
        ["arg", "0"],
        ["sha512_256"]
    ]

def test_sha512_256_invalid():
    with pytest.raises(TealTypeError):
        Sha512_256(Int(1))

def test_keccak256():
    expr = Keccak256(Arg(0))
    assert expr.__teal__() == [
        ["arg", "0"],
        ["keccak256"]
    ]

def test_keccak256_invalid():
    with pytest.raises(TealTypeError):
        Keccak256(Int(1))
