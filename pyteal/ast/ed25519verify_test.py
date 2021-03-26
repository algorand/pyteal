import pytest

from .. import *

def test_ed25519verify():
    args = [Bytes("data"), Bytes("sig"), Bytes("key")]
    expr = Ed25519Verify(args[0], args[1], args[2])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([
        TealOp(args[0], Op.byte, "\"data\""),
        TealOp(args[1], Op.byte, "\"sig\""),
        TealOp(args[2], Op.byte, "\"key\""),
        TealOp(expr, Op.ed25519verify)
    ])

    actual, _ = expr.__teal__()
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)
    
    assert actual == expected

def test_ed25519verify_invalid():
    with pytest.raises(TealTypeError):
        Ed25519Verify(Int(0), Bytes("sig"), Bytes("key"))
    
    with pytest.raises(TealTypeError):
        Ed25519Verify(Bytes("data"), Int(0), Bytes("key"))
    
    with pytest.raises(TealTypeError):
        Ed25519Verify(Bytes("data"), Bytes("sig"), Int(0))
