import pytest

import pyteal as pt

avm2Options = pt.CompileOptions(version=2)
avm3Options = pt.CompileOptions(version=3)
avm4Options = pt.CompileOptions(version=4)
avm5Options = pt.CompileOptions(version=5)


def test_add():
    args = [pt.Int(2), pt.Int(3)]
    expr = pt.Add(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 2),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(expr, pt.Op.add),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_add_overload():
    args = [pt.Int(2), pt.Int(3), pt.Int(4)]
    expr = args[0] + args[1] + args[2]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 2),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(None, pt.Op.add),
            pt.TealOp(args[2], pt.Op.int, 4),
            pt.TealOp(None, pt.Op.add),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_add_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Add(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Add(pt.Txn.sender(), pt.Int(2))


def test_minus():
    args = [pt.Int(5), pt.Int(6)]
    expr = pt.Minus(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 5),
            pt.TealOp(args[1], pt.Op.int, 6),
            pt.TealOp(expr, pt.Op.minus),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_minus_overload():
    args = [pt.Int(10), pt.Int(1), pt.Int(2)]
    expr = args[0] - args[1] - args[2]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 10),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(None, pt.Op.minus),
            pt.TealOp(args[2], pt.Op.int, 2),
            pt.TealOp(None, pt.Op.minus),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_minus_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Minus(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Minus(pt.Txn.sender(), pt.Int(2))


def test_mul():
    args = [pt.Int(3), pt.Int(8)]
    expr = pt.Mul(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 3),
            pt.TealOp(args[1], pt.Op.int, 8),
            pt.TealOp(expr, pt.Op.mul),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_mul_overload():
    args = [pt.Int(3), pt.Int(8), pt.Int(10)]
    expr = args[0] * args[1] * args[2]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 3),
            pt.TealOp(args[1], pt.Op.int, 8),
            pt.TealOp(None, pt.Op.mul),
            pt.TealOp(args[2], pt.Op.int, 10),
            pt.TealOp(None, pt.Op.mul),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_mul_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Mul(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Mul(pt.Txn.sender(), pt.Int(2))


def test_div():
    args = [pt.Int(9), pt.Int(3)]
    expr = pt.Div(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 9),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(expr, pt.Op.div),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_div_overload():
    args = [pt.Int(9), pt.Int(3), pt.Int(3)]
    expr = args[0] / args[1] / args[2]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 9),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(None, pt.Op.div),
            pt.TealOp(args[2], pt.Op.int, 3),
            pt.TealOp(None, pt.Op.div),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_div_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Div(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Div(pt.Txn.sender(), pt.Int(2))


def test_mod():
    args = [pt.Int(10), pt.Int(9)]
    expr = pt.Mod(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 10),
            pt.TealOp(args[1], pt.Op.int, 9),
            pt.TealOp(expr, pt.Op.mod),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_mod_overload():
    args = [pt.Int(10), pt.Int(9), pt.Int(100)]
    expr = args[0] % args[1] % args[2]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 10),
            pt.TealOp(args[1], pt.Op.int, 9),
            pt.TealOp(None, pt.Op.mod),
            pt.TealOp(args[2], pt.Op.int, 100),
            pt.TealOp(None, pt.Op.mod),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_mod_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Mod(pt.Txn.receiver(), pt.Int(2))

    with pytest.raises(pt.TealTypeError):
        pt.Mod(pt.Int(2), pt.Txn.sender())


def test_exp():
    args = [pt.Int(2), pt.Int(9)]
    expr = pt.Exp(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 2),
            pt.TealOp(args[1], pt.Op.int, 9),
            pt.TealOp(expr, pt.Op.exp),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_exp_overload():
    args = [pt.Int(2), pt.Int(3), pt.Int(1)]
    # this is equivalent to args[0] ** (args[1] ** args[2])
    expr = args[0] ** args[1] ** args[2]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 2),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(args[2], pt.Op.int, 1),
            pt.TealOp(None, pt.Op.exp),
            pt.TealOp(None, pt.Op.exp),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_exp_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Exp(pt.Txn.receiver(), pt.Int(2))

    with pytest.raises(pt.TealTypeError):
        pt.Exp(pt.Int(2), pt.Txn.sender())


def test_arithmetic():
    args = [pt.Int(2), pt.Int(3), pt.Int(5), pt.Int(6), pt.Int(8), pt.Int(9)]
    v = ((args[0] + args[1]) / ((args[2] - args[3]) * args[4])) % args[5]
    assert v.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 2),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(None, pt.Op.add),
            pt.TealOp(args[2], pt.Op.int, 5),
            pt.TealOp(args[3], pt.Op.int, 6),
            pt.TealOp(None, pt.Op.minus),
            pt.TealOp(args[4], pt.Op.int, 8),
            pt.TealOp(None, pt.Op.mul),
            pt.TealOp(None, pt.Op.div),
            pt.TealOp(args[5], pt.Op.int, 9),
            pt.TealOp(None, pt.Op.mod),
        ]
    )

    actual, _ = v.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_bitwise_and():
    args = [pt.Int(1), pt.Int(2)]
    expr = pt.BitwiseAnd(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 2),
            pt.TealOp(expr, pt.Op.bitwise_and),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitwise_and_overload():
    args = [pt.Int(1), pt.Int(2), pt.Int(4)]
    expr = args[0] & args[1] & args[2]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 2),
            pt.TealOp(None, pt.Op.bitwise_and),
            pt.TealOp(args[2], pt.Op.int, 4),
            pt.TealOp(None, pt.Op.bitwise_and),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_bitwise_and_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BitwiseAnd(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BitwiseAnd(pt.Txn.sender(), pt.Int(2))


def test_bitwise_or():
    args = [pt.Int(1), pt.Int(2)]
    expr = pt.BitwiseOr(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 2),
            pt.TealOp(expr, pt.Op.bitwise_or),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitwise_or_overload():
    args = [pt.Int(1), pt.Int(2), pt.Int(4)]
    expr = args[0] | args[1] | args[2]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 2),
            pt.TealOp(None, pt.Op.bitwise_or),
            pt.TealOp(args[2], pt.Op.int, 4),
            pt.TealOp(None, pt.Op.bitwise_or),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_bitwise_or_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BitwiseOr(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BitwiseOr(pt.Txn.sender(), pt.Int(2))


def test_bitwise_xor():
    args = [pt.Int(1), pt.Int(3)]
    expr = pt.BitwiseXor(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(expr, pt.Op.bitwise_xor),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitwise_xor_overload():
    args = [pt.Int(1), pt.Int(3), pt.Int(5)]
    expr = args[0] ^ args[1] ^ args[2]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(None, pt.Op.bitwise_xor),
            pt.TealOp(args[2], pt.Op.int, 5),
            pt.TealOp(None, pt.Op.bitwise_xor),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_bitwise_xor_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BitwiseXor(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BitwiseXor(pt.Txn.sender(), pt.Int(2))


def test_shift_left():
    args = [pt.Int(5), pt.Int(1)]
    expr = pt.ShiftLeft(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 5),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.shl),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_shift_left_overload():
    args = [pt.Int(5), pt.Int(1), pt.Int(2)]
    expr = args[0] << args[1] << args[2]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 5),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(None, pt.Op.shl),
            pt.TealOp(args[2], pt.Op.int, 2),
            pt.TealOp(None, pt.Op.shl),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_shift_left_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.ShiftLeft(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.ShiftLeft(pt.Txn.sender(), pt.Int(2))


def test_shift_right():
    args = [pt.Int(5), pt.Int(1)]
    expr = pt.ShiftRight(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 5),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.shr),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_shift_right_overload():
    args = [pt.Int(5), pt.Int(1), pt.Int(2)]
    expr = args[0] >> args[1] >> args[2]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 5),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(None, pt.Op.shr),
            pt.TealOp(args[2], pt.Op.int, 2),
            pt.TealOp(None, pt.Op.shr),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_shift_right_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.ShiftRight(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.ShiftRight(pt.Txn.sender(), pt.Int(2))


def test_eq():
    args_int = [pt.Int(2), pt.Int(3)]
    expr_int = pt.Eq(args_int[0], args_int[1])
    assert expr_int.type_of() == pt.TealType.uint64

    expected_int = pt.TealSimpleBlock(
        [
            pt.TealOp(args_int[0], pt.Op.int, 2),
            pt.TealOp(args_int[1], pt.Op.int, 3),
            pt.TealOp(expr_int, pt.Op.eq),
        ]
    )

    actual_int, _ = expr_int.__teal__(avm2Options)
    actual_int.addIncoming()
    actual_int = pt.TealBlock.NormalizeBlocks(actual_int)

    assert actual_int == expected_int

    args_bytes = [pt.Txn.receiver(), pt.Txn.sender()]
    expr_bytes = pt.Eq(args_bytes[0], args_bytes[1])
    assert expr_bytes.type_of() == pt.TealType.uint64

    expected_bytes = pt.TealSimpleBlock(
        [
            pt.TealOp(args_bytes[0], pt.Op.txn, "Receiver"),
            pt.TealOp(args_bytes[1], pt.Op.txn, "Sender"),
            pt.TealOp(expr_bytes, pt.Op.eq),
        ]
    )

    actual_bytes, _ = expr_bytes.__teal__(avm2Options)
    actual_bytes.addIncoming()
    actual_bytes = pt.TealBlock.NormalizeBlocks(actual_bytes)

    assert actual_bytes == expected_bytes


def test_eq_overload():
    args_int = [pt.Int(2), pt.Int(3)]
    expr_int = args_int[0] == args_int[1]
    assert expr_int.type_of() == pt.TealType.uint64

    expected_int = pt.TealSimpleBlock(
        [
            pt.TealOp(args_int[0], pt.Op.int, 2),
            pt.TealOp(args_int[1], pt.Op.int, 3),
            pt.TealOp(expr_int, pt.Op.eq),
        ]
    )

    actual_int, _ = expr_int.__teal__(avm2Options)
    actual_int.addIncoming()
    actual_int = pt.TealBlock.NormalizeBlocks(actual_int)

    assert actual_int == expected_int

    args_bytes = [pt.Txn.receiver(), pt.Txn.sender()]
    expr_bytes = args_bytes[0] == args_bytes[1]
    assert expr_bytes.type_of() == pt.TealType.uint64

    expected_bytes = pt.TealSimpleBlock(
        [
            pt.TealOp(args_bytes[0], pt.Op.txn, "Receiver"),
            pt.TealOp(args_bytes[1], pt.Op.txn, "Sender"),
            pt.TealOp(expr_bytes, pt.Op.eq),
        ]
    )

    actual_bytes, _ = expr_bytes.__teal__(avm2Options)
    actual_bytes.addIncoming()
    actual_bytes = pt.TealBlock.NormalizeBlocks(actual_bytes)

    assert actual_bytes == expected_bytes


def test_eq_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Eq(pt.Txn.fee(), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Eq(pt.Txn.sender(), pt.Int(7))


def test_neq():
    args_int = [pt.Int(2), pt.Int(3)]
    expr_int = pt.Neq(args_int[0], args_int[1])
    assert expr_int.type_of() == pt.TealType.uint64

    expected_int = pt.TealSimpleBlock(
        [
            pt.TealOp(args_int[0], pt.Op.int, 2),
            pt.TealOp(args_int[1], pt.Op.int, 3),
            pt.TealOp(expr_int, pt.Op.neq),
        ]
    )

    actual_int, _ = expr_int.__teal__(avm2Options)
    actual_int.addIncoming()
    actual_int = pt.TealBlock.NormalizeBlocks(actual_int)

    assert actual_int == expected_int

    args_bytes = [pt.Txn.receiver(), pt.Txn.sender()]
    expr_bytes = pt.Neq(args_bytes[0], args_bytes[1])
    assert expr_bytes.type_of() == pt.TealType.uint64

    expected_bytes = pt.TealSimpleBlock(
        [
            pt.TealOp(args_bytes[0], pt.Op.txn, "Receiver"),
            pt.TealOp(args_bytes[1], pt.Op.txn, "Sender"),
            pt.TealOp(expr_bytes, pt.Op.neq),
        ]
    )

    actual_bytes, _ = expr_bytes.__teal__(avm2Options)
    actual_bytes.addIncoming()
    actual_bytes = pt.TealBlock.NormalizeBlocks(actual_bytes)

    assert actual_bytes == expected_bytes


def test_neq_overload():
    args_int = [pt.Int(2), pt.Int(3)]
    expr_int = args_int[0] != args_int[1]
    assert expr_int.type_of() == pt.TealType.uint64

    expected_int = pt.TealSimpleBlock(
        [
            pt.TealOp(args_int[0], pt.Op.int, 2),
            pt.TealOp(args_int[1], pt.Op.int, 3),
            pt.TealOp(expr_int, pt.Op.neq),
        ]
    )

    actual_int, _ = expr_int.__teal__(avm2Options)
    actual_int.addIncoming()
    actual_int = pt.TealBlock.NormalizeBlocks(actual_int)

    assert actual_int == expected_int

    args_bytes = [pt.Txn.receiver(), pt.Txn.sender()]
    expr_bytes = args_bytes[0] != args_bytes[1]
    assert expr_bytes.type_of() == pt.TealType.uint64

    expected_bytes = pt.TealSimpleBlock(
        [
            pt.TealOp(args_bytes[0], pt.Op.txn, "Receiver"),
            pt.TealOp(args_bytes[1], pt.Op.txn, "Sender"),
            pt.TealOp(expr_bytes, pt.Op.neq),
        ]
    )

    actual_bytes, _ = expr_bytes.__teal__(avm2Options)
    actual_bytes.addIncoming()
    actual_bytes = pt.TealBlock.NormalizeBlocks(actual_bytes)

    assert actual_bytes == expected_bytes


def test_neq_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Neq(pt.Txn.fee(), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Neq(pt.Txn.sender(), pt.Int(7))


def test_lt():
    args = [pt.Int(2), pt.Int(3)]
    expr = pt.Lt(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 2),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(expr, pt.Op.lt),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_lt_overload():
    args = [pt.Int(2), pt.Int(3)]
    expr = args[0] < args[1]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 2),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(expr, pt.Op.lt),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_lt_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Lt(pt.Int(7), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Lt(pt.Txn.sender(), pt.Int(7))


def test_le():
    args = [pt.Int(1), pt.Int(2)]
    expr = pt.Le(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 2),
            pt.TealOp(expr, pt.Op.le),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_le_overload():
    args = [pt.Int(1), pt.Int(2)]
    expr = args[0] <= args[1]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 2),
            pt.TealOp(expr, pt.Op.le),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_le_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Le(pt.Int(1), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Le(pt.Txn.sender(), pt.Int(1))


def test_gt():
    args = [pt.Int(2), pt.Int(3)]
    expr = pt.Gt(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 2),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(expr, pt.Op.gt),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gt_overload():
    args = [pt.Int(2), pt.Int(3)]
    expr = args[0] > args[1]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 2),
            pt.TealOp(args[1], pt.Op.int, 3),
            pt.TealOp(expr, pt.Op.gt),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gt_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Gt(pt.Int(1), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Gt(pt.Txn.receiver(), pt.Int(1))


def test_ge():
    args = [pt.Int(1), pt.Int(10)]
    expr = pt.Ge(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 10),
            pt.TealOp(expr, pt.Op.ge),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_ge_overload():
    args = [pt.Int(1), pt.Int(10)]
    expr = args[0] >= args[1]
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 1),
            pt.TealOp(args[1], pt.Op.int, 10),
            pt.TealOp(expr, pt.Op.ge),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_ge_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Ge(pt.Int(1), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.Ge(pt.Txn.receiver(), pt.Int(1))


def test_get_bit_int():
    args = [pt.Int(3), pt.Int(1)]
    expr = pt.GetBit(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 3),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.getbit),
        ]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm2Options)


def test_get_bit_bytes():
    args = [pt.Bytes("base16", "0xFF"), pt.Int(1)]
    expr = pt.GetBit(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFF"),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.getbit),
        ]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm2Options)


def test_get_bit_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.GetBit(pt.Int(3), pt.Bytes("index"))

    with pytest.raises(pt.TealTypeError):
        pt.GetBit(pt.Bytes("base16", "0xFF"), pt.Bytes("index"))


def test_get_byte():
    args = [pt.Bytes("base16", "0xFF"), pt.Int(0)]
    expr = pt.GetByte(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFF"),
            pt.TealOp(args[1], pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.getbyte),
        ]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm2Options)


def test_get_byte_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.GetByte(pt.Int(3), pt.Int(0))

    with pytest.raises(pt.TealTypeError):
        pt.GetBit(pt.Bytes("base16", "0xFF"), pt.Bytes("index"))


def test_b_add():
    args = [
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFE"),
    ]
    expr = pt.BytesAdd(args[0], args[1])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(args[1], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFE"),
            pt.TealOp(expr, pt.Op.b_add),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_add_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesAdd(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesAdd(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_minus():
    args = [
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFE"),
    ]
    expr = pt.BytesMinus(args[0], args[1])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(args[1], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFE"),
            pt.TealOp(expr, pt.Op.b_minus),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_minus_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesMinus(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesMinus(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_div():
    args = [pt.Bytes("base16", "0xFFFFFFFFFFFFFFFF00"), pt.Bytes("base16", "0xFF")]
    expr = pt.BytesDiv(args[0], args[1])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFF00"),
            pt.TealOp(args[1], pt.Op.byte, "0xFF"),
            pt.TealOp(expr, pt.Op.b_div),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_div_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesDiv(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesDiv(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_mul():
    args = [pt.Bytes("base16", "0xFFFFFFFFFFFFFFFF"), pt.Bytes("base16", "0xFF")]
    expr = pt.BytesMul(args[0], args[1])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFF"),
            pt.TealOp(args[1], pt.Op.byte, "0xFF"),
            pt.TealOp(expr, pt.Op.b_mul),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_mul_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesMul(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesMul(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_mod():
    args = [pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"), pt.Bytes("base16", "0xFF")]
    expr = pt.BytesMod(args[0], args[1])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(args[1], pt.Op.byte, "0xFF"),
            pt.TealOp(expr, pt.Op.b_mod),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_mod_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesMod(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesMod(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_and():
    args = [pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"), pt.Bytes("base16", "0xFF")]
    expr = pt.BytesAnd(args[0], args[1])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            pt.TealOp(args[1], pt.Op.byte, "0xFF"),
            pt.TealOp(expr, pt.Op.b_and),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_and_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesAnd(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesAnd(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_or():
    args = [pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"), pt.Bytes("base16", "0xFF")]
    expr = pt.BytesOr(args[0], args[1])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            pt.TealOp(args[1], pt.Op.byte, "0xFF"),
            pt.TealOp(expr, pt.Op.b_or),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_or_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesOr(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesOr(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_xor():
    args = [pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"), pt.Bytes("base16", "0xFF")]
    expr = pt.BytesXor(args[0], args[1])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            pt.TealOp(args[1], pt.Op.byte, "0xFF"),
            pt.TealOp(expr, pt.Op.b_xor),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_xor_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesXor(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesXor(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_eq():
    args = [
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
    ]
    expr = pt.BytesEq(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(args[1], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(expr, pt.Op.b_eq),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_eq_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesEq(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesEq(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_neq():
    args = [
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
    ]
    expr = pt.BytesNeq(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(args[1], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(expr, pt.Op.b_neq),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_neq_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesNeq(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesNeq(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_lt():
    args = [
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"),
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
    ]
    expr = pt.BytesLt(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            pt.TealOp(args[1], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(expr, pt.Op.b_lt),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_lt_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesLt(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesLt(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_le():
    args = [
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"),
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
    ]
    expr = pt.BytesLe(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            pt.TealOp(args[1], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(expr, pt.Op.b_le),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_le_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesLe(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesLe(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_gt():
    args = [
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"),
    ]
    expr = pt.BytesGt(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(args[1], pt.Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            pt.TealOp(expr, pt.Op.b_gt),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_gt_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesGt(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesGt(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_b_ge():
    args = [
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
        pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFF0"),
    ]
    expr = pt.BytesGe(args[0], args[1])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(args[1], pt.Op.byte, "0xFFFFFFFFFFFFFFFFF0"),
            pt.TealOp(expr, pt.Op.b_ge),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm3Options)


def test_b_ge_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesGe(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.BytesGe(pt.Bytes("base16", "0xFF"), pt.Int(2))


def test_extract_uint():
    for expression, op in (
        (pt.ExtractUint16, pt.Op.extract_uint16),
        (pt.ExtractUint32, pt.Op.extract_uint32),
        (pt.ExtractUint64, pt.Op.extract_uint64),
    ):
        args = [
            pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF"),
            pt.Int(2),
        ]
        expr = expression(args[0], args[1])
        assert expr.type_of() == pt.TealType.uint64

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(args[0], pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
                pt.TealOp(args[1], pt.Op.int, 2),
                pt.TealOp(expr, op),
            ]
        )

        actual, _ = expr.__teal__(avm5Options)
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        assert actual == expected

        with pytest.raises(pt.TealInputError):
            expr.__teal__(avm4Options)


def test_extract_uint_invalid():
    for expression in (pt.ExtractUint16, pt.ExtractUint32, pt.ExtractUint64):
        with pytest.raises(pt.TealTypeError):
            expression(pt.Int(2), pt.Txn.receiver())

        with pytest.raises(pt.TealTypeError):
            expression(pt.Bytes("base16", "0xFF"), pt.Txn.receiver())
