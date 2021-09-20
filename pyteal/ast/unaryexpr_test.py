import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

teal2Options = CompileOptions(version=2)
teal3Options = CompileOptions(version=3)
teal4Options = CompileOptions(version=4)
teal5Options = CompileOptions(version=5)


def test_btoi():
    arg = Arg(1)
    expr = Btoi(arg)
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(arg, Op.arg, 1), TealOp(expr, Op.btoi)])

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

    expected = TealSimpleBlock([TealOp(arg, Op.int, 1), TealOp(expr, Op.itob)])

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

    expected = TealSimpleBlock([TealOp(arg, Op.txn, "Receiver"), TealOp(expr, Op.len)])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_len_invalid():
    with pytest.raises(TealTypeError):
        Len(Int(1))


def test_bitlen_int():
    arg = Int(7)
    expr = BitLen(arg)
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(arg, Op.int, 7), TealOp(expr, Op.bitlen)])

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitlen_bytes():
    arg = Txn.receiver()
    expr = BitLen(arg)
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(arg, Op.txn, "Receiver"), TealOp(expr, Op.bitlen)]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_sha256():
    arg = Arg(0)
    expr = Sha256(arg)
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(arg, Op.arg, 0), TealOp(expr, Op.sha256)])

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

    expected = TealSimpleBlock([TealOp(arg, Op.arg, 0), TealOp(expr, Op.sha512_256)])

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

    expected = TealSimpleBlock([TealOp(arg, Op.arg, 0), TealOp(expr, Op.keccak256)])

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

    expected = TealSimpleBlock([TealOp(arg, Op.int, 1), TealOp(expr, Op.logic_not)])

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

    expected = TealSimpleBlock([TealOp(arg, Op.int, 2), TealOp(expr, Op.bitwise_not)])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitwise_not_overload():
    arg = Int(10)
    expr = ~arg
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(arg, Op.int, 10), TealOp(expr, Op.bitwise_not)])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_bitwise_not_invalid():
    with pytest.raises(TealTypeError):
        BitwiseNot(Txn.receiver())


def test_sqrt():
    arg = Int(4)
    expr = Sqrt(arg)
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(arg, Op.int, 4), TealOp(expr, Op.sqrt)])

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_sqrt_invalid():
    with pytest.raises(TealTypeError):
        Sqrt(Txn.receiver())


def test_pop():
    arg_int = Int(3)
    expr_int = Pop(arg_int)
    assert expr_int.type_of() == TealType.none

    expected_int = TealSimpleBlock(
        [TealOp(arg_int, Op.int, 3), TealOp(expr_int, Op.pop)]
    )

    actual_int, _ = expr_int.__teal__(teal2Options)
    actual_int.addIncoming()
    actual_int = TealBlock.NormalizeBlocks(actual_int)

    assert actual_int == expected_int

    arg_bytes = Txn.receiver()
    expr_bytes = Pop(arg_bytes)
    assert expr_bytes.type_of() == TealType.none

    expected_bytes = TealSimpleBlock(
        [TealOp(arg_bytes, Op.txn, "Receiver"), TealOp(expr_bytes, Op.pop)]
    )

    actual_bytes, _ = expr_bytes.__teal__(teal2Options)
    actual_bytes.addIncoming()
    actual_bytes = TealBlock.NormalizeBlocks(actual_bytes)

    assert actual_bytes == expected_bytes


def test_pop_invalid():
    expr = Pop(Int(0))
    with pytest.raises(TealTypeError):
        Pop(expr)


def test_balance():
    arg = Int(0)
    expr = Balance(arg)
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(arg, Op.int, 0), TealOp(expr, Op.balance)])

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_balance_direct_ref():
    arg = Txn.sender()
    expr = Balance(arg)
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(arg, Op.txn, "Sender"), TealOp(expr, Op.balance)]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_balance_invalid():
    with pytest.raises(TealTypeError):
        args = [Txn.sender(), Int(17)]
        expr = AssetHolding.balance(args[0], args[1])
        MinBalance(expr)


def test_min_balance():
    arg = Int(0)
    expr = MinBalance(arg)
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(arg, Op.int, 0), TealOp(expr, Op.min_balance)])

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_min_balance_direct_ref():
    arg = Txn.sender()
    expr = MinBalance(arg)
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [TealOp(arg, Op.txn, "Sender"), TealOp(expr, Op.min_balance)]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_min_balance_invalid():
    with pytest.raises(TealTypeError):
        args = [Txn.sender(), Int(17)]
        expr = AssetHolding.balance(args[0], args[1])
        MinBalance(expr)


def test_b_not():
    arg = Bytes("base16", "0xFFFFFFFFFFFFFFFFFF")
    expr = BytesNot(arg)
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [TealOp(arg, Op.byte, "0xFFFFFFFFFFFFFFFFFF"), TealOp(expr, Op.b_not)]
    )

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_b_not_invalid():
    with pytest.raises(TealTypeError):
        BytesNot(Int(2))


def test_b_zero():
    arg = Int(8)
    expr = BytesZero(arg)
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(arg, Op.int, 8), TealOp(expr, Op.bzero)])

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_b_zero_invalid():
    with pytest.raises(TealTypeError):
        BytesZero(Bytes("base16", "0x11"))


def test_log():
    arg = Bytes("message")
    expr = Log(arg)
    assert expr.type_of() == TealType.none
    assert not expr.has_return()

    expected = TealSimpleBlock(
        [TealOp(arg, Op.byte, '"message"'), TealOp(expr, Op.log)]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_log_invalid():
    with pytest.raises(TealTypeError):
        Log(Int(7))
