import pytest

from ..errors import TealTypeError
from . import *

def test_cond():
    Cond([Int(1), Int(2)], [Int(0), Int(2)])
    Cond([Int(1), Int(2)])
    Cond([Int(1), Int(2)], [Int(2), Int(3)], [Int(3), Int(4)])

    with pytest.raises(TealTypeError):
        Cond([Int(1), Int(2)],
             [Int(2), Txn.receiver()])

    with pytest.raises(TealTypeError):
        Cond([Arg(0), Int(2)])
