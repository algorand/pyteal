import pytest

from ..errors import TealInputError
from . import *

def test_nonce():
    Nonce("base32", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M", Int(1))
    Nonce("base32", "", Int(1))
    Nonce("base64", "Zm9vYmE=", Int(1))
    Nonce("base64", "", Int(1))
    Nonce("base16", "A21212EF", Int(1))
    Nonce("base16", "0xA21212EF", Int(1))
    Nonce("base16", "", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base23", "", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base32", "Zm9vYmE=", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base64", "?????", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base16", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M", Int(1))
