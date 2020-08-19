import pytest

from .. import *

def test_btoi():
    expr = Btoi(Arg(1))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.arg, 1),
        TealOp(Op.btoi)
    ]

def test_btoi_invalid():
    with pytest.raises(TealTypeError):
        Btoi(Int(1))

def test_itob():
    expr = Itob(Int(1))
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.itob)
    ]

def test_itob_invalid():
    with pytest.raises(TealTypeError):
        Itob(Arg(1))

def test_len():
    expr = Len(Txn.receiver())
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.txn, "Receiver"),
        TealOp(Op.len)
    ]

def test_len_invalid():
    with pytest.raises(TealTypeError):
        Len(Int(1))

def test_sha256():
    expr = Sha256(Arg(0))
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.arg, 0),
        TealOp(Op.sha256)
    ]

def test_sha256_invalid():
    with pytest.raises(TealTypeError):
        Sha256(Int(1))

def test_sha512_256():
    expr = Sha512_256(Arg(0))
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.arg, 0),
        TealOp(Op.sha512_256)
    ]

def test_sha512_256_invalid():
    with pytest.raises(TealTypeError):
        Sha512_256(Int(1))

def test_keccak256():
    expr = Keccak256(Arg(0))
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.arg, 0),
        TealOp(Op.keccak256)
    ]

def test_keccak256_invalid():
    with pytest.raises(TealTypeError):
        Keccak256(Int(1))

def test_not():
    expr = Not(Int(1))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.logic_not)
    ]

def test_not_invalid():
    with pytest.raises(TealTypeError):
        Not(Txn.receiver())

def test_bitwise_not():
    expr = BitwiseNot(Int(2))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.bitwise_not)
    ]

def test_bitwise_not_overload():
    expr = ~Int(10)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 10),
        TealOp(Op.bitwise_not)
    ]

def test_bitwise_not_invalid():
    with pytest.raises(TealTypeError):
        BitwiseNot(Txn.receiver())

def test_pop():
    expr_int = Pop(Int(3))
    assert expr_int.type_of() == TealType.none
    assert expr_int.__teal__() == [
        TealOp(Op.int, 3),
        TealOp(Op.pop)
    ]

    expr_bytes = Pop(Txn.receiver())
    assert expr_bytes.type_of() == TealType.none
    assert expr_bytes.__teal__() == [
        TealOp(Op.txn, "Receiver"),
        TealOp(Op.pop)
    ]

def test_pop_invalid():
    expr = Pop(Int(0))
    with pytest.raises(TealTypeError):
        Pop(expr)

def test_return():
    expr = Return(Int(1))
    assert expr.type_of() == TealType.none
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.return_)
    ]

def test_return_invalid():
    with pytest.raises(TealTypeError):
        Return(Txn.receiver())

def test_balance():
    expr = Balance(Int(0))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 0),
        TealOp(Op.balance)
    ]

def test_balance_invalid():
    with pytest.raises(TealTypeError):
        Balance(Txn.receiver())
