import pytest

from .. import *

def test_substring():
    args = [Bytes("my string"), Int(0), Int(2)]
    expr = Substring(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([
        TealOp(args[0], Op.byte, "\"my string\""),
        TealOp(args[1], Op.int, 0),
        TealOp(args[2], Op.int, 2),
        TealOp(expr, Op.substring3)
    ])

    actual, _ = expr.__teal__()
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_substring_invalid():
    with pytest.raises(TealTypeError):
        Substring(Int(0), Int(0), Int(2))
    
    with pytest.raises(TealTypeError):
        Substring(Bytes("my string"), Txn.sender(), Int(2))
    
    with pytest.raises(TealTypeError):
        Substring(Bytes("my string"), Int(0), Txn.sender())
