import pytest

from .. import *

def test_add():
    expr = Add(Int(2), Int(3))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.add)
    ]

def test_add_overload():
    expr = Int(2) + Int(3) + Int(4)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.add),
        TealOp(Op.int, 4),
        TealOp(Op.add)
    ]

def test_add_invalid():
    with pytest.raises(TealTypeError):
        Add(Int(2), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Add(Txn.sender(), Int(2))

def test_minus():
    expr = Minus(Int(5), Int(6))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 5),
        TealOp(Op.int, 6),
        TealOp(Op.minus)
    ]

def test_minus_overload():
    expr = Int(10) - Int(1) - Int(2)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 10),
        TealOp(Op.int, 1),
        TealOp(Op.minus),
        TealOp(Op.int, 2),
        TealOp(Op.minus)
    ]

def test_minus_invalid():
    with pytest.raises(TealTypeError):
        Minus(Int(2), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Minus(Txn.sender(), Int(2))

def test_mul():
    expr = Mul(Int(3), Int(8))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 3),
        TealOp(Op.int, 8),
        TealOp(Op.mul)
    ]

def test_mul_overload():
    expr = Int(3) * Int(8) * Int(10)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 3),
        TealOp(Op.int, 8),
        TealOp(Op.mul),
        TealOp(Op.int, 10),
        TealOp(Op.mul)
    ]

def test_mul_invalid():
    with pytest.raises(TealTypeError):
        Mul(Int(2), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Mul(Txn.sender(), Int(2))

def test_div():
    expr = Div(Int(9), Int(3))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 9),
        TealOp(Op.int, 3),
        TealOp(Op.div)
    ]

def test_div_overload():
    expr = Int(9) / Int(3) / Int(3)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 9),
        TealOp(Op.int, 3),
        TealOp(Op.div),
        TealOp(Op.int, 3),
        TealOp(Op.div),
    ]

def test_div_invalid():
    with pytest.raises(TealTypeError):
        Div(Int(2), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Div(Txn.sender(), Int(2))

def test_mod():
    expr = Mod(Int(10), Int(9))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 10),
        TealOp(Op.int, 9),
        TealOp(Op.mod)
    ]

def test_mod_overload():
    expr = Int(10) % Int(9) % Int(100)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 10),
        TealOp(Op.int, 9),
        TealOp(Op.mod),
        TealOp(Op.int, 100),
        TealOp(Op.mod)
    ]

def test_mod_invalid():
    with pytest.raises(TealTypeError):
        Mod(Txn.receiver(), Int(2))
    
    with pytest.raises(TealTypeError):
        Mod(Int(2), Txn.sender())

def test_arithmetic():
    v = ((Int(2) + Int(3))/((Int(5) - Int(6)) * Int(8))) % Int(9)
    assert v.type_of() == TealType.uint64
    assert v.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.add),
        TealOp(Op.int, 5),
        TealOp(Op.int, 6),
        TealOp(Op.minus),
        TealOp(Op.int, 8),
        TealOp(Op.mul),
        TealOp(Op.div),
        TealOp(Op.int, 9),
        TealOp(Op.mod)
    ]

def test_bitwise_and():
    expr = BitwiseAnd(Int(1), Int(2))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 2),
        TealOp(Op.bitwise_and)
    ]

def test_bitwise_and_overload():
    expr = Int(1) & Int(2) & Int(4)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 2),
        TealOp(Op.bitwise_and),
        TealOp(Op.int, 4),
        TealOp(Op.bitwise_and)
    ]

def test_bitwise_and_invalid():
    with pytest.raises(TealTypeError):
        BitwiseAnd(Int(2), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        BitwiseAnd(Txn.sender(), Int(2))

def test_bitwise_or():
    expr = BitwiseOr(Int(1), Int(2))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 2),
        TealOp(Op.bitwise_or)
    ]

def test_bitwise_or_overload():
    expr = Int(1) | Int(2) | Int(4)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 2),
        TealOp(Op.bitwise_or),
        TealOp(Op.int, 4),
        TealOp(Op.bitwise_or)
    ]

def test_bitwise_or_invalid():
    with pytest.raises(TealTypeError):
        BitwiseOr(Int(2), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        BitwiseOr(Txn.sender(), Int(2))

def test_bitwise_xor():
    expr = BitwiseXor(Int(1), Int(3))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 3),
        TealOp(Op.bitwise_xor)
    ]

def test_bitwise_xor_overload():
    expr = Int(1) ^ Int(3) ^ Int(5)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 3),
        TealOp(Op.bitwise_xor),
        TealOp(Op.int, 5),
        TealOp(Op.bitwise_xor)
    ]

def test_bitwise_xor_invalid():
    with pytest.raises(TealTypeError):
        BitwiseXor(Int(2), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        BitwiseXor(Txn.sender(), Int(2))

def test_eq():
    expr_int = Eq(Int(2), Int(3))
    assert expr_int.type_of() == TealType.uint64
    assert expr_int.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.eq)
    ]

    expr_bytes = Eq(Txn.receiver(), Txn.sender())
    assert expr_bytes.type_of() == TealType.uint64
    assert expr_bytes.__teal__() == [
        TealOp(Op.txn, "Receiver"),
        TealOp(Op.txn, "Sender"),
        TealOp(Op.eq)
    ]

def test_eq_overload():
    expr_int = Int(2) == Int(3)
    assert expr_int.type_of() == TealType.uint64
    assert expr_int.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.eq)
    ]

    expr_bytes = Txn.receiver() == Txn.sender()
    assert expr_bytes.type_of() == TealType.uint64
    assert expr_bytes.__teal__() == [
        TealOp(Op.txn, "Receiver"),
        TealOp(Op.txn, "Sender"),
        TealOp(Op.eq)
    ]

def test_eq_invalid():
    with pytest.raises(TealTypeError):
        Eq(Txn.fee(), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Eq(Txn.sender(), Int(7))

def test_neq():
    expr_int = Neq(Int(2), Int(3))
    assert expr_int.type_of() == TealType.uint64
    assert expr_int.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.neq)
    ]

    expr_bytes = Neq(Txn.receiver(), Txn.sender())
    assert expr_bytes.type_of() == TealType.uint64
    assert expr_bytes.__teal__() == [
        TealOp(Op.txn, "Receiver"),
        TealOp(Op.txn, "Sender"),
        TealOp(Op.neq)
    ]

def test_neq_overload():
    expr_int = Int(2) != Int(3)
    assert expr_int.type_of() == TealType.uint64
    assert expr_int.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.neq)
    ]

    expr_bytes = Txn.receiver() != Txn.sender()
    assert expr_bytes.type_of() == TealType.uint64
    assert expr_bytes.__teal__() == [
        TealOp(Op.txn, "Receiver"),
        TealOp(Op.txn, "Sender"),
        TealOp(Op.neq)
    ]

def test_neq_invalid():
    with pytest.raises(TealTypeError):
        Neq(Txn.fee(), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Neq(Txn.sender(), Int(7))

def test_lt():
    expr = Lt(Int(2), Int(3))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.lt)
    ]

def test_lt_overload():
    expr = Int(2) < Int(3)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.lt)
    ]

def test_lt_invalid():
    with pytest.raises(TealTypeError):
        Lt(Int(7), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Lt(Txn.sender(), Int(7))

def test_le():
    expr = Le(Int(1), Int(2))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 2),
        TealOp(Op.le)
    ]

def test_le_overload():
    expr = Int(1) <= Int(2)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 2),
        TealOp(Op.le)
    ]

def test_le_invalid():
    with pytest.raises(TealTypeError):
        Le(Int(1), Txn.receiver())

    with pytest.raises(TealTypeError):
        Le(Txn.sender(), Int(1))

def test_gt():
    expr = Gt(Int(2), Int(3))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.gt)
    ]

def test_gt_overload():
    expr = Int(2) > Int(3)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 2),
        TealOp(Op.int, 3),
        TealOp(Op.gt)
    ]

def test_gt_invalid():
    with pytest.raises(TealTypeError):
        Gt(Int(1), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Gt(Txn.receiver(), Int(1))

def test_ge():
    expr = Ge(Int(1), Int(10))
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 10),
        TealOp(Op.ge)
    ]

def test_ge_overload():
    expr = Int(1) >= Int(10)
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, 1),
        TealOp(Op.int, 10),
        TealOp(Op.ge)
    ]

def test_ge_invalid():
    with pytest.raises(TealTypeError):
        Ge(Int(1), Txn.receiver())
    
    with pytest.raises(TealTypeError):
        Ge(Txn.receiver(), Int(1))
