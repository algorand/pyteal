import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_nonce_has_return():
    exprWithReturn = Nonce(
        "base32",
        "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M",
        Return(Int(1)),
    )
    assert exprWithReturn.has_return()

    exprWithoutReturn = Nonce(
        "base32", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M", Int(1)
    )
    assert not exprWithoutReturn.has_return()


def test_nonce_base32():
    arg = Int(1)
    expr = Nonce(
        "base32", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M", arg
    )
    assert expr.type_of() == TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = TealSimpleBlock(
        [
            TealOp(
                actual.ops[0].expr,
                Op.byte,
                "base32(7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M)",
            ),
            TealOp(actual.ops[1].expr, Op.pop),
            TealOp(arg, Op.int, 1),
        ]
    )

    assert actual == expected


def test_nonce_base32_empty():
    arg = Int(1)
    expr = Nonce("base32", "", arg)
    assert expr.type_of() == TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = TealSimpleBlock(
        [
            TealOp(actual.ops[0].expr, Op.byte, "base32()"),
            TealOp(actual.ops[1].expr, Op.pop),
            TealOp(arg, Op.int, 1),
        ]
    )

    assert actual == expected


def test_nonce_base64():
    arg = Txn.sender()
    expr = Nonce("base64", "Zm9vYmE=", arg)
    assert expr.type_of() == TealType.bytes

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = TealSimpleBlock(
        [
            TealOp(actual.ops[0].expr, Op.byte, "base64(Zm9vYmE=)"),
            TealOp(actual.ops[1].expr, Op.pop),
            TealOp(arg, Op.txn, "Sender"),
        ]
    )

    assert actual == expected


def test_nonce_base64_empty():
    arg = Int(1)
    expr = Nonce("base64", "", arg)
    assert expr.type_of() == TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = TealSimpleBlock(
        [
            TealOp(actual.ops[0].expr, Op.byte, "base64()"),
            TealOp(actual.ops[1].expr, Op.pop),
            TealOp(arg, Op.int, 1),
        ]
    )

    assert actual == expected


def test_nonce_base16():
    arg = Int(1)
    expr = Nonce("base16", "A21212EF", arg)
    assert expr.type_of() == TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = TealSimpleBlock(
        [
            TealOp(actual.ops[0].expr, Op.byte, "0xA21212EF"),
            TealOp(actual.ops[1].expr, Op.pop),
            TealOp(arg, Op.int, 1),
        ]
    )

    assert actual == expected


def test_nonce_base16_prefix():
    arg = Int(1)
    expr = Nonce("base16", "0xA21212EF", arg)
    assert expr.type_of() == TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = TealSimpleBlock(
        [
            TealOp(actual.ops[0].expr, Op.byte, "0xA21212EF"),
            TealOp(actual.ops[1].expr, Op.pop),
            TealOp(arg, Op.int, 1),
        ]
    )

    assert actual == expected


def test_nonce_base16_empty():
    arg = Int(6)
    expr = Nonce("base16", "", arg)
    assert expr.type_of() == TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = TealSimpleBlock(
        [
            TealOp(actual.ops[0].expr, Op.byte, "0x"),
            TealOp(actual.ops[1].expr, Op.pop),
            TealOp(arg, Op.int, 6),
        ]
    )

    assert actual == expected


def test_nonce_invalid():
    with pytest.raises(TealInputError):
        Nonce("base23", "", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base32", "Zm9vYmE=", Int(1))

    with pytest.raises(TealInputError):
        Nonce("base64", "?????", Int(1))

    with pytest.raises(TealInputError):
        Nonce(
            "base16",
            "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M",
            Int(1),
        )
