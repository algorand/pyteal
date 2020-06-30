import pytest

from .. import *

def test_substring():
    expr = Substring(Bytes("my string"), Int(0), Int(2))
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.byte, "\"my string\""),
        TealOp(Op.int, 0),
        TealOp(Op.int, 2),
        TealOp(Op.substring3)
    ]

def test_substring_invalid():
    with pytest.raises(TealTypeError):
        Substring(Int(0), Int(0), Int(2))
    
    with pytest.raises(TealTypeError):
        Substring(Bytes("my string"), Txn.sender(), Int(2))
    
    with pytest.raises(TealTypeError):
        Substring(Bytes("my string"), Int(0), Txn.sender())
