import pytest

from ..errors import TealTypeError
from . import *

def test_btoi():
    Btoi(Arg(1))

    with pytest.raises(TealTypeError):
        Btoi(Int(1))

def test_itob():
    Itob(Int(1))

    with pytest.raises(TealTypeError):
        Itob(Arg(1))

def test_len():
    Len(Txn.receiver())

    with pytest.raises(TealTypeError):
        Len(Int(1))

def test_sha256():
    Sha256(Arg(0))

    with pytest.raises(TealTypeError):
        Sha256(Int(1))

def test_sha512_256():
    Sha512_256(Arg(0))

    with pytest.raises(TealTypeError):
        Sha512_256(Int(1))

def test_keccak256():
    Keccak256(Arg(0))

    with pytest.raises(TealTypeError):
        Keccak256(Int(1))
