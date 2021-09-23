import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

teal2Options = CompileOptions(version=2)
teal3Options = CompileOptions(version=3)
teal4Options = CompileOptions(version=4)
teal5Options = CompileOptions(version=5)


def test_ed25519verify():
    args = [Bytes("data"), Bytes("sig"), Bytes("key")]
    expr = Ed25519Verify(args[0], args[1], args[2])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"data"'),
            TealOp(args[1], Op.byte, '"sig"'),
            TealOp(args[2], Op.byte, '"key"'),
            TealOp(expr, Op.ed25519verify),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
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


def test_substring():
    args = [Bytes("my string"), Int(0), Int(2)]
    expr = Substring(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"my string"'),
            TealOp(args[1], Op.int, 0),
            TealOp(args[2], Op.int, 2),
            TealOp(expr, Op.substring3),
        ]
    )

    actual, _ = expr.__teal__(teal2Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_substring_invalid():
    with pytest.raises(TealTypeError):
        Substring(Int(0), Int(0), Int(2))

    with pytest.raises(TealTypeError):
        Substring(Bytes("my string"), Txn.sender(), Int(2))

    with pytest.raises(TealTypeError):
        Substring(Bytes("my string"), Int(0), Txn.sender())


def test_extract():
    args = [Bytes("my string"), Int(0), Int(2)]
    expr = Extract(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, '"my string"'),
            TealOp(args[1], Op.int, 0),
            TealOp(args[2], Op.int, 2),
            TealOp(expr, Op.extract3),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal4Options)


def test_extract_invalid():
    with pytest.raises(TealTypeError):
        Extract(Int(0), Int(0), Int(2))

    with pytest.raises(TealTypeError):
        Extract(Bytes("my string"), Txn.sender(), Int(2))

    with pytest.raises(TealTypeError):
        Extract(Bytes("my string"), Int(0), Txn.sender())


def test_set_bit_int():
    args = [Int(0), Int(2), Int(1)]
    expr = SetBit(args[0], args[1], args[2])
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.int, 0),
            TealOp(args[1], Op.int, 2),
            TealOp(args[2], Op.int, 1),
            TealOp(expr, Op.setbit),
        ]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_set_bit_bytes():
    args = [Bytes("base16", "0x0000"), Int(0), Int(1)]
    expr = SetBit(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0x0000"),
            TealOp(args[1], Op.int, 0),
            TealOp(args[2], Op.int, 1),
            TealOp(expr, Op.setbit),
        ]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_set_bit_invalid():
    with pytest.raises(TealTypeError):
        SetBit(Int(3), Bytes("index"), Int(1))

    with pytest.raises(TealTypeError):
        SetBit(Int(3), Int(0), Bytes("one"))

    with pytest.raises(TealTypeError):
        SetBit(Bytes("base16", "0xFF"), Bytes("index"), Int(1))

    with pytest.raises(TealTypeError):
        SetBit(Bytes("base16", "0xFF"), Int(0), Bytes("one"))


def test_set_byte():
    args = [Bytes("base16", "0xFF"), Int(0), Int(3)]
    expr = SetByte(args[0], args[1], args[2])
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock(
        [
            TealOp(args[0], Op.byte, "0xFF"),
            TealOp(args[1], Op.int, 0),
            TealOp(args[2], Op.int, 3),
            TealOp(expr, Op.setbyte),
        ]
    )

    actual, _ = expr.__teal__(teal3Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(TealInputError):
        expr.__teal__(teal2Options)


def test_set_byte_invalid():
    with pytest.raises(TealTypeError):
        SetByte(Int(3), Int(0), Int(1))

    with pytest.raises(TealTypeError):
        SetByte(Bytes("base16", "0xFF"), Bytes("index"), Int(1))

    with pytest.raises(TealTypeError):
        SetByte(Bytes("base16", "0xFF"), Int(0), Bytes("one"))
