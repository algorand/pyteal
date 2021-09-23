import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

teal2Options = CompileOptions(version=2)
teal3Options = CompileOptions(version=3)
teal4Options = CompileOptions(version=4)
teal5Options = CompileOptions(version=5)


def test_add():
    args = [Int(2), Int(3)]
    expr = Add(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 2), TealOp(args[1], Op.int, 3), TealOp(expr, Op.add)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_add_overload():
    args = [Int(2), Int(3), Int(4)]
    expr = args[0] + args[1] + args[2]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 2),
            TealOp(args[1], Op.int, 3),
            TealOp(None, Op.add),
            TealOp(args[2], Op.int, 4),
            TealOp(None, Op.add),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_add_invalid():
    with pytest.raises(TealTypeError):
        Add(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        Add(Txn.sender(), Int(2))


def test_minus():
    args = [Int(5), Int(6)]
    expr = Minus(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 5), TealOp(args[1], Op.int, 6), TealOp(expr, Op.minus)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_minus_overload():
    args = [Int(10), Int(1), Int(2)]
    expr = args[0] - args[1] - args[2]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 10),
            TealOp(args[1], Op.int, 1),
            TealOp(None, Op.minus),
            TealOp(args[2], Op.int, 2),
            TealOp(None, Op.minus),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_minus_invalid():
    with pytest.raises(TealTypeError):
        Minus(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        Minus(Txn.sender(), Int(2))


def test_mul():
    args = [Int(3), Int(8)]
    expr = Mul(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 3), TealOp(args[1], Op.int, 8), TealOp(expr, Op.mul)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_mul_overload():
    args = [Int(3), Int(8), Int(10)]
    expr = args[0] * args[1] * args[2]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 3),
            TealOp(args[1], Op.int, 8),
            TealOp(None, Op.mul),
            TealOp(args[2], Op.int, 10),
            TealOp(None, Op.mul),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_mul_invalid():
    with pytest.raises(TealTypeError):
        Mul(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        Mul(Txn.sender(), Int(2))


def test_div():
    args = [Int(9), Int(3)]
    expr = Div(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 9), TealOp(args[1], Op.int, 3), TealOp(expr, Op.div)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_div_overload():
    args = [Int(9), Int(3), Int(3)]
    expr = args[0] / args[1] / args[2]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 9),
            TealOp(args[1], Op.int, 3),
            TealOp(None, Op.div),
            TealOp(args[2], Op.int, 3),
            TealOp(None, Op.div),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_div_invalid():
    with pytest.raises(TealTypeError):
        Div(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        Div(Txn.sender(), Int(2))


def test_mod():
    args = [Int(10), Int(9)]
    expr = Mod(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 10), TealOp(args[1], Op.int, 9), TealOp(expr, Op.mod)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_mod_overload():
    args = [Int(10), Int(9), Int(100)]
    expr = args[0] % args[1] % args[2]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 10),
            TealOp(args[1], Op.int, 9),
            TealOp(None, Op.mod),
            TealOp(args[2], Op.int, 100),
            TealOp(None, Op.mod),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_mod_invalid():
    with pytest.raises(TealTypeError):
        Mod(Txn.receiver(), Int(2))

    with pytest.raises(TealTypeError):
        Mod(Int(2), Txn.sender())


def test_exp():
    args = [Int(2), Int(9)]
    expr = Exp(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 2), TealOp(args[1], Op.int, 9), TealOp(expr, Op.exp)]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_exp_overload():
    args = [Int(2), Int(3), Int(1)]
    # this is equivalent to args[0] ** (args[1] ** args[2])
    expr = args[0] ** args[1] ** args[2]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 2),
            TealOp(args[1], Op.int, 3),
            TealOp(args[2], Op.int, 1),
            TealOp(None, Op.exp),
            TealOp(None, Op.exp),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_exp_invalid():
    with pytest.raises(TealTypeError):
        Exp(Txn.receiver(), Int(2))

    with pytest.raises(TealTypeError):
        Exp(Int(2), Txn.sender())


def test_arithmetic():
    args = [Int(2), Int(3), Int(5), Int(6), Int(8), Int(9)]
    v = ((args[0] + args[1]) / ((args[2] - args[3]) * args[4])) % args[5]
    assert v.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 2),
            TealOp(args[1], Op.int, 3),
            TealOp(None, Op.add),
            TealOp(args[2], Op.int, 5),
            TealOp(args[3], Op.int, 6),
            TealOp(None, Op.minus),
            TealOp(args[4], Op.int, 8),
            TealOp(None, Op.mul),
            TealOp(None, Op.div),
            TealOp(args[5], Op.int, 9),
            TealOp(None, Op.mod),
        ]
    )

    actual, _ = v.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_bitwise_and():
    args = [Int(1), Int(2)]
    expr = BitwiseAnd(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 2),
            TealOp(expr, Op.bitwise_and),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitwise_and_overload():
    args = [Int(1), Int(2), Int(4)]
    expr = args[0] & args[1] & args[2]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 2),
            TealOp(None, Op.bitwise_and),
            TealOp(args[2], Op.int, 4),
            TealOp(None, Op.bitwise_and),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_bitwise_and_invalid():
    with pytest.raises(TealTypeError):
        BitwiseAnd(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BitwiseAnd(Txn.sender(), Int(2))


def test_bitwise_or():
    args = [Int(1), Int(2)]
    expr = BitwiseOr(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 2),
            TealOp(expr, Op.bitwise_or),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitwise_or_overload():
    args = [Int(1), Int(2), Int(4)]
    expr = args[0] | args[1] | args[2]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 2),
            TealOp(None, Op.bitwise_or),
            TealOp(args[2], Op.int, 4),
            TealOp(None, Op.bitwise_or),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_bitwise_or_invalid():
    with pytest.raises(TealTypeError):
        BitwiseOr(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BitwiseOr(Txn.sender(), Int(2))


def test_bitwise_xor():
    args = [Int(1), Int(3)]
    expr = BitwiseXor(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 3),
            TealOp(expr, Op.bitwise_xor),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitwise_xor_overload():
    args = [Int(1), Int(3), Int(5)]
    expr = args[0] ^ args[1] ^ args[2]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 1),
            TealOp(args[1], Op.int, 3),
            TealOp(None, Op.bitwise_xor),
            TealOp(args[2], Op.int, 5),
            TealOp(None, Op.bitwise_xor),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_bitwise_xor_invalid():
    with pytest.raises(TealTypeError):
        BitwiseXor(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BitwiseXor(Txn.sender(), Int(2))


def test_shift_left():
    args = [Int(5), Int(1)]
    expr = ShiftLeft(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 5), TealOp(args[1], Op.int, 1), TealOp(expr, Op.shl)]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_shift_left_overload():
    args = [Int(5), Int(1), Int(2)]
    expr = args[0] << args[1] << args[2]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 5),
            TealOp(args[1], Op.int, 1),
            TealOp(None, Op.shl),
            TealOp(args[2], Op.int, 2),
            TealOp(None, Op.shl),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_shift_left_invalid():
    with pytest.raises(TealTypeError):
        ShiftLeft(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        ShiftLeft(Txn.sender(), Int(2))


def test_shift_right():
    args = [Int(5), Int(1)]
    expr = ShiftRight(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 5), TealOp(args[1], Op.int, 1), TealOp(expr, Op.shr)]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_shift_right_overload():
    args = [Int(5), Int(1), Int(2)]
    expr = args[0] >> args[1] >> args[2]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 5),
            TealOp(args[1], Op.int, 1),
            TealOp(None, Op.shr),
            TealOp(args[2], Op.int, 2),
            TealOp(None, Op.shr),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    with TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_shift_right_invalid():
    with pytest.raises(TealTypeError):
        ShiftRight(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        ShiftRight(Txn.sender(), Int(2))


def test_eq():
    args_int = [Int(2), Int(3)]
    expr_int = Eq(args_int[0], args_int[1])
    assert expr_int.type_of() == TealType.uint64

    expected_int = TealSimpleBlock(
        [
            TealOp(args_int[0], Op.int, 2),
            TealOp(args_int[1], Op.int, 3),
            TealOp(expr_int, Op.eq),
        ]
    )

    actual_int, _ = expr_int.__teal__(teal2Options)
    actual_int.addIncoming()
    actual_int = TealBlock.NormalizeBlocks(actual_int)

    assert actual_int == expected_int

    args_bytes = [Txn.receiver(), Txn.sender()]
    expr_bytes = Eq(args_bytes[0], args_bytes[1])
    assert expr_bytes.type_of() == TealType.uint64

    expected_bytes = TealSimpleBlock(
        [
            TealOp(args_bytes[0], Op.txn, "Receiver"),
            TealOp(args_bytes[1], Op.txn, "Sender"),
            TealOp(expr_bytes, Op.eq),
        ]
    )

    actual_bytes, _ = expr_bytes.__teal__(teal2Options)
    actual_bytes.addIncoming()
    actual_bytes = TealBlock.NormalizeBlocks(actual_bytes)

    assert actual_bytes == expected_bytes


def test_eq_overload():
    args_int = [Int(2), Int(3)]
    expr_int = args_int[0] == args_int[1]
    assert expr_int.type_of() == TealType.uint64

    expected_int = TealSimpleBlock(
        [
            TealOp(args_int[0], Op.int, 2),
            TealOp(args_int[1], Op.int, 3),
            TealOp(expr_int, Op.eq),
        ]
    )

    actual_int, _ = expr_int.__teal__(teal2Options)
    actual_int.addIncoming()
    actual_int = TealBlock.NormalizeBlocks(actual_int)

    assert actual_int == expected_int

    args_bytes = [Txn.receiver(), Txn.sender()]
    expr_bytes = args_bytes[0] == args_bytes[1]
    assert expr_bytes.type_of() == TealType.uint64

    expected_bytes = TealSimpleBlock(
        [
            TealOp(args_bytes[0], Op.txn, "Receiver"),
            TealOp(args_bytes[1], Op.txn, "Sender"),
            TealOp(expr_bytes, Op.eq),
        ]
    )

    actual_bytes, _ = expr_bytes.__teal__(teal2Options)
    actual_bytes.addIncoming()
    actual_bytes = TealBlock.NormalizeBlocks(actual_bytes)

    assert actual_bytes == expected_bytes


def test_eq_invalid():
    with pytest.raises(TealTypeError):
        Eq(Txn.fee(), Txn.receiver())

    with pytest.raises(TealTypeError):
        Eq(Txn.sender(), Int(7))


def test_neq():
    args_int = [Int(2), Int(3)]
    expr_int = Neq(args_int[0], args_int[1])
    assert expr_int.type_of() == TealType.uint64

    expected_int = TealSimpleBlock(
        [
            TealOp(args_int[0], Op.int, 2),
            TealOp(args_int[1], Op.int, 3),
            TealOp(expr_int, Op.neq),
        ]
    )

    actual_int, _ = expr_int.__teal__(teal2Options)
    actual_int.addIncoming()
    actual_int = TealBlock.NormalizeBlocks(actual_int)

    assert actual_int == expected_int

    args_bytes = [Txn.receiver(), Txn.sender()]
    expr_bytes = Neq(args_bytes[0], args_bytes[1])
    assert expr_bytes.type_of() == TealType.uint64

    expected_bytes = TealSimpleBlock(
        [
            TealOp(args_bytes[0], Op.txn, "Receiver"),
            TealOp(args_bytes[1], Op.txn, "Sender"),
            TealOp(expr_bytes, Op.neq),
        ]
    )

    actual_bytes, _ = expr_bytes.__teal__(teal2Options)
    actual_bytes.addIncoming()
    actual_bytes = TealBlock.NormalizeBlocks(actual_bytes)

    assert actual_bytes == expected_bytes


def test_neq_overload():
    args_int = [Int(2), Int(3)]
    expr_int = args_int[0] != args_int[1]
    assert expr_int.type_of() == TealType.uint64

    expected_int = TealSimpleBlock(
        [
            TealOp(args_int[0], Op.int, 2),
            TealOp(args_int[1], Op.int, 3),
            TealOp(expr_int, Op.neq),
        ]
    )

    actual_int, _ = expr_int.__teal__(teal2Options)
    actual_int.addIncoming()
    actual_int = TealBlock.NormalizeBlocks(actual_int)

    assert actual_int == expected_int

    args_bytes = [Txn.receiver(), Txn.sender()]
    expr_bytes = args_bytes[0] != args_bytes[1]
    assert expr_bytes.type_of() == TealType.uint64

    expected_bytes = TealSimpleBlock(
        [
            TealOp(args_bytes[0], Op.txn, "Receiver"),
            TealOp(args_bytes[1], Op.txn, "Sender"),
            TealOp(expr_bytes, Op.neq),
        ]
    )

    actual_bytes, _ = expr_bytes.__teal__(teal2Options)
    actual_bytes.addIncoming()
    actual_bytes = TealBlock.NormalizeBlocks(actual_bytes)

    assert actual_bytes == expected_bytes


def test_neq_invalid():
    with pytest.raises(TealTypeError):
        Neq(Txn.fee(), Txn.receiver())

    with pytest.raises(TealTypeError):
        Neq(Txn.sender(), Int(7))


def test_lt():
    args = [Int(2), Int(3)]
    expr = Lt(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 2), TealOp(args[1], Op.int, 3), TealOp(expr, Op.lt)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_lt_overload():
    args = [Int(2), Int(3)]
    expr = args[0] < args[1]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 2), TealOp(args[1], Op.int, 3), TealOp(expr, Op.lt)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_lt_invalid():
    with pytest.raises(TealTypeError):
        Lt(Int(7), Txn.receiver())

    with pytest.raises(TealTypeError):
        Lt(Txn.sender(), Int(7))


def test_le():
    args = [Int(1), Int(2)]
    expr = Le(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 1), TealOp(args[1], Op.int, 2), TealOp(expr, Op.le)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_le_overload():
    args = [Int(1), Int(2)]
    expr = args[0] <= args[1]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 1), TealOp(args[1], Op.int, 2), TealOp(expr, Op.le)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_le_invalid():
    with pytest.raises(TealTypeError):
        Le(Int(1), Txn.receiver())

    with pytest.raises(TealTypeError):
        Le(Txn.sender(), Int(1))


def test_gt():
    args = [Int(2), Int(3)]
    expr = Gt(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 2), TealOp(args[1], Op.int, 3), TealOp(expr, Op.gt)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gt_overload():
    args = [Int(2), Int(3)]
    expr = args[0] > args[1]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 2), TealOp(args[1], Op.int, 3), TealOp(expr, Op.gt)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gt_invalid():
    with pytest.raises(TealTypeError):
        Gt(Int(1), Txn.receiver())

    with pytest.raises(TealTypeError):
        Gt(Txn.receiver(), Int(1))


def test_ge():
    args = [Int(1), Int(10)]
    expr = Ge(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 1), TealOp(args[1], Op.int, 10), TealOp(expr, Op.ge)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_ge_overload():
    args = [Int(1), Int(10)]
    expr = args[0] >= args[1]
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(args[0], Op.int, 1), TealOp(args[1], Op.int, 10), TealOp(expr, Op.ge)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_ge_invalid():
    with pytest.raises(TealTypeError):
        Ge(Int(1), Txn.receiver())

    with pytest.raises(TealTypeError):
        Ge(Txn.receiver(), Int(1))


def test_get_bit_int():
    args = [Int(3), Int(1)]
    expr = GetBit(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 3),
            TealOp(args[1], Op.int, 1),
            TealOp(expr, Op.getbit),
        ]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_get_bit_bytes():
    args = [Bytes("base16", "0xFF"), Int(1)]
    expr = GetBit(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFF"),
            TealOp(args[1], Op.int, 1),
            TealOp(expr, Op.getbit),
        ]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_get_bit_invalid():
    with pytest.raises(TealTypeError):
        GetBit(Int(3), Bytes("index"))

    with pytest.raises(TealTypeError):
        GetBit(Bytes("base16", "0xFF"), Bytes("index"))


def test_get_byte():
    args = [Bytes("base16", "0xFF"), Int(0)]
    expr = GetByte(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFF"),
            TealOp(args[1], Op.int, 0),
            TealOp(expr, Op.getbyte),
        ]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_get_byte_invalid():
    with pytest.raises(TealTypeError):
        GetByte(Int(3), Int(0))

    with pytest.raises(TealTypeError):
        GetBit(Bytes("base16", "0xFF"), Bytes("index"))


def test_b_add():
    args = [
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFE"),
    ]
    expr = BytesAdd(args[0], args[1])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            TealOp(args[1], Op.byte, "0xFFFFFFFFFFFFFFFFFE"),
            TealOp(expr, Op.b_add),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_add_invalid():
    with pytest.raises(TealTypeError):
        BytesAdd(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesAdd(Bytes("base16", "0xFF"), Int(2))


def test_b_minus():
    args = [
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFE"),
    ]
    expr = BytesMinus(args[0], args[1])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            TealOp(args[1], Op.byte, "0xFFFFFFFFFFFFFFFFFE"),
            TealOp(expr, Op.b_minus),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_minus_invalid():
    with pytest.raises(TealTypeError):
        BytesMinus(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesMinus(Bytes("base16", "0xFF"), Int(2))


def test_b_div():
    args = [Bytes("base16", "0xFFFFFFFFFFFFFFFF00"), Bytes("base16", "0xFF")]
    expr = BytesDiv(args[0], args[1])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFF00"),
            TealOp(args[1], Op.byte, "0xFF"),
            TealOp(expr, Op.b_div),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_div_invalid():
    with pytest.raises(TealTypeError):
        BytesDiv(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesDiv(Bytes("base16", "0xFF"), Int(2))


def test_b_mul():
    args = [Bytes("base16", "0xFFFFFFFFFFFFFFFF"), Bytes("base16", "0xFF")]
    expr = BytesMul(args[0], args[1])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFF"),
            TealOp(args[1], Op.byte, "0xFF"),
            TealOp(expr, Op.b_mul),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_mul_invalid():
    with pytest.raises(TealTypeError):
        BytesMul(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesMul(Bytes("base16", "0xFF"), Int(2))


def test_b_mod():
    args = [Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"), Bytes("base16", "0xFF")]
    expr = BytesMod(args[0], args[1])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            TealOp(args[1], Op.byte, "0xFF"),
            TealOp(expr, Op.b_mod),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_mod_invalid():
    with pytest.raises(TealTypeError):
        BytesMod(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesMod(Bytes("base16", "0xFF"), Int(2))


def test_b_and():
    args = [Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"), Bytes("base16", "0xFF")]
    expr = BytesAnd(args[0], args[1])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            TealOp(args[1], Op.byte, "0xFF"),
            TealOp(expr, Op.b_and),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_and_invalid():
    with pytest.raises(TealTypeError):
        BytesAnd(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesAnd(Bytes("base16", "0xFF"), Int(2))


def test_b_or():
    args = [Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"), Bytes("base16", "0xFF")]
    expr = BytesOr(args[0], args[1])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            TealOp(args[1], Op.byte, "0xFF"),
            TealOp(expr, Op.b_or),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_or_invalid():
    with pytest.raises(TealTypeError):
        BytesOr(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesOr(Bytes("base16", "0xFF"), Int(2))


def test_b_xor():
    args = [Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"), Bytes("base16", "0xFF")]
    expr = BytesXor(args[0], args[1])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            TealOp(args[1], Op.byte, "0xFF"),
            TealOp(expr, Op.b_xor),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_xor_invalid():
    with pytest.raises(TealTypeError):
        BytesXor(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesXor(Bytes("base16", "0xFF"), Int(2))


def test_b_eq():
    args = [
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
    ]
    expr = BytesEq(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            TealOp(args[1], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            TealOp(expr, Op.b_eq),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_eq_invalid():
    with pytest.raises(TealTypeError):
        BytesEq(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesEq(Bytes("base16", "0xFF"), Int(2))


def test_b_neq():
    args = [
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
    ]
    expr = BytesNeq(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            TealOp(args[1], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            TealOp(expr, Op.b_neq),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_neq_invalid():
    with pytest.raises(TealTypeError):
        BytesNeq(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesNeq(Bytes("base16", "0xFF"), Int(2))


def test_b_lt():
    args = [
        Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"),
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
    ]
    expr = BytesLt(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            TealOp(args[1], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            TealOp(expr, Op.b_lt),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_lt_invalid():
    with pytest.raises(TealTypeError):
        BytesLt(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesLt(Bytes("base16", "0xFF"), Int(2))


def test_b_le():
    args = [
        Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"),
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
    ]
    expr = BytesLe(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            TealOp(args[1], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            TealOp(expr, Op.b_le),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_le_invalid():
    with pytest.raises(TealTypeError):
        BytesLe(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesLe(Bytes("base16", "0xFF"), Int(2))


def test_b_gt():
    args = [
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"),
    ]
    expr = BytesGt(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            TealOp(args[1], Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            TealOp(expr, Op.b_gt),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_gt_invalid():
    with pytest.raises(TealTypeError):
        BytesGt(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesGt(Bytes("base16", "0xFF"), Int(2))


def test_b_ge():
    args = [
        Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"),
    ]
    expr = BytesGe(args[0], args[1])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            TealOp(args[1], Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            TealOp(expr, Op.b_ge),
        ]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal3Options)


def test_b_ge_invalid():
    with pytest.raises(TealTypeError):
        BytesGe(Int(2), Txn.receiver())

    with pytest.raises(TealTypeError):
        BytesGe(Bytes("base16", "0xFF"), Int(2))


def test_extract_uint():
    for expression, op in (
        (ExtractUint16, Op.extract_uint16),
        (ExtractUint32, Op.extract_uint32),
        (ExtractUint64, Op.extract_uint64),
    ):
        args = [
            Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
            Int(2),
        ]
        expr = expression(args[0], args[1])
        assert expr.type_of() == TealType.uint64

        expected = TealSimpleBlock(
            [
                TealOp(args[0], Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
                TealOp(args[1], Op.int, 2),
                TealOp(expr, op),
            ]
        )

        actual, _ = expr.__teal__(teal5Options)
        actual.addIncoming()
        actual = TealBlock.NormalizeBlocks(actual)

        assert actual == expected

        with pytest.raises(TealInputError):
            expr.__teal__(teal4Options)


def test_extract_uint_invalid():
    for expression in (ExtractUint16, ExtractUint32, ExtractUint64):
        with pytest.raises(TealTypeError):
            expression(Int(2), Txn.receiver())

        with pytest.raises(TealTypeError):
            expression(Bytes("base16", "0xFF"), Txn.receiver())
