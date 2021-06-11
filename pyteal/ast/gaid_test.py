import pytest

from .. import *

teal3Options = CompileOptions(version=3)
teal4Options = CompileOptions(version=4)

def test_gaid_teal_3():
    with pytest.raises(TealInputError):
        GeneratedID(0).__teal__(teal3Options)

def test_gaid():
    expr = GeneratedID(0)
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([
        TealOp(expr, Op.gaid, 0)
    ])
    
    actual, _ = expr.__teal__(teal4Options)

    assert actual == expected

def test_gaid_invalid():
    with pytest.raises(TealInputError):
        GeneratedID(-1)

def test_gaid_dynamic_teal_3():
    with pytest.raises(TealInputError):
        GeneratedID(Int(0)).__teal__(teal3Options)

def test_gaid_dynamic():
    arg = Int(0)
    expr = GeneratedID(arg)
    assert expr.type_of() == TealType.uint64
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.int, 0),
        TealOp(expr, Op.gaids)
    ])

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_gaid_dynamic_invalid():
    with pytest.raises(TealTypeError):
        GeneratedID(Bytes("index"))
