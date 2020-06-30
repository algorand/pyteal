import pytest

from .. import *

def test_ed25519verify():
    expr = Ed25519Verify(Bytes("data"), Bytes("sig"), Bytes("key"))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.byte, "\"data\""),
        TealOp(Op.byte, "\"sig\""),
        TealOp(Op.byte, "\"key\""),
        TealOp(Op.ed25519verify)
    ]

def test_ed25519verify_invalid():
    with pytest.raises(TealTypeError):
        Ed25519Verify(Int(0), Bytes("sig"), Bytes("key"))
    
    with pytest.raises(TealTypeError):
        Ed25519Verify(Bytes("data"), Int(0), Bytes("key"))
    
    with pytest.raises(TealTypeError):
        Ed25519Verify(Bytes("data"), Bytes("sig"), Int(0))
