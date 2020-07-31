import pytest

from ..errors import TealTypeError
from . import *

def test_if():
    If(Int(0), Txn.sender(), Txn.receiver())

    with pytest.raises(TealTypeError):
        If(Int(0), Txn.amount(), Txn.sender())

    with pytest.raises(TealTypeError):
        If(Txn.sender(), Int(1), Int(0))
