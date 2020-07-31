import pytest

from ..errors import TealTypeError, TealInputError
from ..compiler import compileTeal
from . import *

def test_and():
    p1 = And(Int(1), Int(1))
    p2 = Int(1).And(Int(1))
    assert compileTeal(p1) == compileTeal(p2)

    p3 = And(Int(1), Int(1), Int(2))
    assert p3.__teal__() == \
    [['int', '1'], ['int', '1'], ['&&'], ['int', '2'], ['&&']]
    
    with pytest.raises(TealTypeError):
        And(Int(1), Txn.receiver())

    with pytest.raises(TealInputError):
        And(Int(1))

def test_or():
    p1 = Or(Int(1), Int(0))
    p2 = Int(1).Or(Int(0))
    assert compileTeal(p1) == compileTeal(p2)

    p3 = Or(Int(0), Int(1), Int(2))
    assert p3.__teal__() == \
        [['int', '0'], ['int', '1'], ['||'], ['int', '2'], ['||']]
    
    with pytest.raises(TealTypeError):
        Or(Int(1), Txn.receiver())
