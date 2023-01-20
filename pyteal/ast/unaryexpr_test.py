import pytest

import pyteal as pt

avm2Options = pt.CompileOptions(version=2)
avm3Options = pt.CompileOptions(version=3)
avm4Options = pt.CompileOptions(version=4)
avm5Options = pt.CompileOptions(version=5)
avm6Options = pt.CompileOptions(version=6)
avm7Options = pt.CompileOptions(version=7)


def test_btoi():
    arg = pt.Arg(1)
    expr = pt.Btoi(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.arg, 1), pt.TealOp(expr, pt.Op.btoi)]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_btoi_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Btoi(pt.Int(1))


def test_itob():
    arg = pt.Int(1)
    expr = pt.Itob(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 1), pt.TealOp(expr, pt.Op.itob)]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_itob_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Itob(pt.Arg(1))


def test_len():
    arg = pt.Txn.receiver()
    expr = pt.Len(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.txn, "Receiver"), pt.TealOp(expr, pt.Op.len)]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_len_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Len(pt.Int(1))


def test_bitlen_int():
    arg = pt.Int(7)
    expr = pt.BitLen(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 7), pt.TealOp(expr, pt.Op.bitlen)]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitlen_bytes():
    arg = pt.Txn.receiver()
    expr = pt.BitLen(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.txn, "Receiver"), pt.TealOp(expr, pt.Op.bitlen)]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_sha256():
    arg = pt.Arg(0)
    expr = pt.Sha256(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.arg, 0), pt.TealOp(expr, pt.Op.sha256)]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_sha256_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Sha256(pt.Int(1))


def test_sha512_256():
    arg = pt.Arg(0)
    expr = pt.Sha512_256(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.arg, 0), pt.TealOp(expr, pt.Op.sha512_256)]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_sha512_256_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Sha512_256(pt.Int(1))


def test_sha3_256():
    arg = pt.Arg(0)
    expr = pt.Sha3_256(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.arg, 0), pt.TealOp(expr, pt.Op.sha3_256)]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_sha3_256_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Sha3_256(pt.Int(1))


def test_keccak256():
    arg = pt.Arg(0)
    expr = pt.Keccak256(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.arg, 0), pt.TealOp(expr, pt.Op.keccak256)]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_keccak256_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Keccak256(pt.Int(1))


def test_not():
    arg = pt.Int(1)
    expr = pt.Not(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 1), pt.TealOp(expr, pt.Op.logic_not)]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_not_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Not(pt.Txn.receiver())


def test_bitwise_not():
    arg = pt.Int(2)
    expr = pt.BitwiseNot(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 2), pt.TealOp(expr, pt.Op.bitwise_not)]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitwise_not_overload():
    arg = pt.Int(10)
    expr = ~arg
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 10), pt.TealOp(expr, pt.Op.bitwise_not)]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitwise_not_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BitwiseNot(pt.Txn.receiver())


def test_sqrt():
    arg = pt.Int(4)
    expr = pt.Sqrt(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 4), pt.TealOp(expr, pt.Op.sqrt)]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_sqrt_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Sqrt(pt.Txn.receiver())


def test_pop():
    arg_int = pt.Int(3)
    expr_int = pt.Pop(arg_int)
    assert expr_int.type_of() == pt.TealType.none

    expected_int = pt.TealSimpleBlock(
        [pt.TealOp(arg_int, pt.Op.int, 3), pt.TealOp(expr_int, pt.Op.pop)]
    )

    actual_int, _ = expr_int.__teal__(avm2Options)
    actual_int.addIncoming()
    actual_int = pt.TealBlock.NormalizeBlocks(actual_int)

    assert actual_int == expected_int

    arg_bytes = pt.Txn.receiver()
    expr_bytes = pt.Pop(arg_bytes)
    assert expr_bytes.type_of() == pt.TealType.none

    expected_bytes = pt.TealSimpleBlock(
        [pt.TealOp(arg_bytes, pt.Op.txn, "Receiver"), pt.TealOp(expr_bytes, pt.Op.pop)]
    )

    actual_bytes, _ = expr_bytes.__teal__(avm2Options)
    actual_bytes.addIncoming()
    actual_bytes = pt.TealBlock.NormalizeBlocks(actual_bytes)

    assert actual_bytes == expected_bytes


def test_pop_invalid():
    expr = pt.Pop(pt.Int(0))
    with pytest.raises(pt.TealTypeError):
        pt.Pop(expr)


def test_balance():
    arg = pt.Int(0)
    expr = pt.Balance(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 0), pt.TealOp(expr, pt.Op.balance)]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_balance_direct_ref():
    arg = pt.Txn.sender()
    expr = pt.Balance(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.txn, "Sender"), pt.TealOp(expr, pt.Op.balance)]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_balance_invalid():
    with pytest.raises(pt.TealTypeError):
        args = [pt.Txn.sender(), pt.Int(17)]
        expr = pt.AssetHolding.balance(args[0], args[1])
        pt.MinBalance(expr)


def test_min_balance():
    arg = pt.Int(0)
    expr = pt.MinBalance(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 0), pt.TealOp(expr, pt.Op.min_balance)]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_min_balance_direct_ref():
    arg = pt.Txn.sender()
    expr = pt.MinBalance(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.txn, "Sender"), pt.TealOp(expr, pt.Op.min_balance)]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_min_balance_invalid():
    with pytest.raises(pt.TealTypeError):
        args = [pt.Txn.sender(), pt.Int(17)]
        expr = pt.AssetHolding.balance(args[0], args[1])
        pt.MinBalance(expr)


def test_b_not():
    arg = pt.Bytes("base16", "0xFFFFFFFFFFFFFFFFFF")
    expr = pt.BytesNot(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.byte, "0xFFFFFFFFFFFFFFFFFF"),
            pt.TealOp(expr, pt.Op.b_not),
        ]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_b_not_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesNot(pt.Int(2))


def test_bsqrt():
    arg = pt.Bytes("base16", "0xFEDCBA9876543210")
    expr = pt.BytesSqrt(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.byte, "0xFEDCBA9876543210"), pt.TealOp(expr, pt.Op.bsqrt)]
    )

    actual, _ = expr.__teal__(avm6Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bsqrt_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesSqrt(pt.Int(2**64 - 1))


def test_b_zero():
    arg = pt.Int(8)
    expr = pt.BytesZero(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 8), pt.TealOp(expr, pt.Op.bzero)]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_b_zero_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.BytesZero(pt.Bytes("base16", "0x11"))


def test_log():
    arg = pt.Bytes("message")
    expr = pt.Log(arg)
    assert expr.type_of() == pt.TealType.none
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.byte, '"message"'), pt.TealOp(expr, pt.Op.log)]
    )

    actual, _ = expr.__teal__(avm5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm4Options)


def test_log_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Log(pt.Int(7))
