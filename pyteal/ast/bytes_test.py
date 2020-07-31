import pytest

from ..errors import TealInputError
from .bytes import Bytes

def test_bytes():
    Bytes("base32", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
    Bytes("base32", "")
    Bytes("base64", "Zm9vYmE=")
    Bytes("base64", "")
    Bytes("base16", "A21212EF")
    Bytes("base16", "0xA21212EF")
    Bytes("base16","")

    with pytest.raises(TealInputError):
        Bytes("base23", "")

    with pytest.raises(TealInputError):
        Bytes("base32", "Zm9vYmE=")

    with pytest.raises(TealInputError):
        Bytes("base64", "?????")

    with pytest.raises(TealInputError):
        Bytes("base16", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
