import pytest

from .. import *
# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

teal2Options = CompileOptions(version=2)
teal3Options = CompileOptions(version=2)

def test_btoi():
    arg = Arg(1)
    expr = Btoi(arg)
    assert expr.type_of() == TealType.uint64
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.arg, 1),
        TealOp(expr, Op.btoi)
    ])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_btoi_invalid():
    with pytest.raises(TealTypeError):
        Btoi(Int(1))

def test_itob():
    arg = Int(1)
    expr = Itob(arg)
    assert expr.type_of() == TealType.bytes
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.int, 1),
        TealOp(expr, Op.itob)
    ])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_itob_invalid():
    with pytest.raises(TealTypeError):
        Itob(Arg(1))

def test_len():
    arg = Txn.receiver()
    expr = Len(arg)
    assert expr.type_of() == TealType.uint64
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.txn, "Receiver"),
        TealOp(expr, Op.len)
    ])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_len_invalid():
    with pytest.raises(TealTypeError):
        Len(Int(1))

def test_sha256():
    arg = Arg(0)
    expr = Sha256(arg)
    assert expr.type_of() == TealType.bytes
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.arg, 0),
        TealOp(expr, Op.sha256)
    ])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_sha256_invalid():
    with pytest.raises(TealTypeError):
        Sha256(Int(1))

def test_sha512_256():
    arg = Arg(0)
    expr = Sha512_256(arg)
    assert expr.type_of() == TealType.bytes
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.arg, 0),
        TealOp(expr, Op.sha512_256)
    ])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_sha512_256_invalid():
    with pytest.raises(TealTypeError):
        Sha512_256(Int(1))

def test_keccak256():
    arg = Arg(0)
    expr = Keccak256(arg)
    assert expr.type_of() == TealType.bytes
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.arg, 0),
        TealOp(expr, Op.keccak256)
    ])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_keccak256_invalid():
    with pytest.raises(TealTypeError):
        Keccak256(Int(1))

def test_not():
    arg = Int(1)
    expr = Not(arg)
    assert expr.type_of() == TealType.uint64
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.int, 1),
        TealOp(expr, Op.logic_not)
    ])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_not_invalid():
    with pytest.raises(TealTypeError):
        Not(Txn.receiver())

def test_bitwise_not():
    arg = Int(2)
    expr = BitwiseNot(arg)
    assert expr.type_of() == TealType.uint64
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.int, 2),
        TealOp(expr, Op.bitwise_not)
    ])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_bitwise_not_overload():
    arg = Int(10)
    expr = ~arg
    assert expr.type_of() == TealType.uint64
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.int, 10),
        TealOp(expr, Op.bitwise_not)
    ])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_bitwise_not_invalid():
    with pytest.raises(TealTypeError):
        BitwiseNot(Txn.receiver())

def test_pop():
    arg_int = Int(3)
    expr_int = Pop(arg_int)
    assert expr_int.type_of() == TealType.none
    
    expected_int = TealSimpleBlock([
        TealOp(arg_int, Op.int, 3),
        TealOp(expr_int, Op.pop)
    ])

    actual_int, _ = expr_int.__teal__(teal2Options)
    actual_int.addIncoming()
    actual_int = TealBlock.NormalizeBlocks(actual_int)
    
    assert actual_int == expected_int

    arg_bytes = Txn.receiver()
    expr_bytes = Pop(arg_bytes)
    assert expr_bytes.type_of() == TealType.none

    expected_bytes = TealSimpleBlock([
        TealOp(arg_bytes, Op.txn, "Receiver"),
        TealOp(expr_bytes, Op.pop)
    ])

    actual_bytes, _ = expr_bytes.__teal__(teal2Options)
    actual_bytes.addIncoming()
    actual_bytes = TealBlock.NormalizeBlocks(actual_bytes)

    assert actual_bytes == expected_bytes

def test_pop_invalid():
    expr = Pop(Int(0))
    with pytest.raises(TealTypeError):
        Pop(expr)

def test_return():
    arg = Int(1)
    expr = Return(arg)
    assert expr.type_of() == TealType.none
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.int, 1),
        TealOp(expr, Op.return_)
    ])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_return_invalid():
    with pytest.raises(TealTypeError):
        Return(Txn.receiver())

def test_balance():
    arg = Int(0)
    expr = Balance(arg)
    assert expr.type_of() == TealType.uint64
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.int, 0),
        TealOp(expr, Op.balance)
    ])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_balance_invalid():
    with pytest.raises(TealTypeError):
        Balance(Txn.receiver())

def test_min_balance():
    arg = Int(0)
    expr = MinBalance(arg)
    assert expr.type_of() == TealType.uint64
    
    expected = TealSimpleBlock([
        TealOp(arg, Op.int, 0),
        TealOp(expr, Op.min_balance)
    ])

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

def test_min_balance_invalid():
    with pytest.raises(TealTypeError):
        MinBalance(Txn.receiver())
