import pytest

from ..errors import TealInputError
from .int import Int

def test_int():
    Int(232323)

    with pytest.raises(TealInputError):
        Int(6.7)

    with pytest.raises(TealInputError):
        Int(-1)

    with pytest.raises(TealInputError):
        Int(2 ** 64)
