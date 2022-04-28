import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_nonce_has_return():
    exprWithReturn = pt.Nonce(
        "base32",
        "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M",
        pt.Return(pt.Int(1)),
    )
    assert exprWithReturn.has_return()

    exprWithoutReturn = pt.Nonce(
        "base32",
        "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M",
        pt.Int(1),
    )
    assert not exprWithoutReturn.has_return()


def test_nonce_base32():
    arg = pt.Int(1)
    expr = pt.Nonce(
        "base32", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M", arg
    )
    assert expr.type_of() == pt.TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(
                actual.ops[0].expr,
                pt.Op.byte,
                "base32(7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M)",
            ),
            pt.TealOp(actual.ops[1].expr, pt.Op.pop),
            pt.TealOp(arg, pt.Op.int, 1),
        ]
    )

    assert actual == expected


def test_nonce_base32_empty():
    arg = pt.Int(1)
    expr = pt.Nonce("base32", "", arg)
    assert expr.type_of() == pt.TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(actual.ops[0].expr, pt.Op.byte, "base32()"),
            pt.TealOp(actual.ops[1].expr, pt.Op.pop),
            pt.TealOp(arg, pt.Op.int, 1),
        ]
    )

    assert actual == expected


def test_nonce_base64():
    arg = pt.Txn.sender()
    expr = pt.Nonce("base64", "Zm9vYmE=", arg)
    assert expr.type_of() == pt.TealType.bytes

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(actual.ops[0].expr, pt.Op.byte, "base64(Zm9vYmE=)"),
            pt.TealOp(actual.ops[1].expr, pt.Op.pop),
            pt.TealOp(arg, pt.Op.txn, "Sender"),
        ]
    )

    assert actual == expected


def test_nonce_base64_empty():
    arg = pt.Int(1)
    expr = pt.Nonce("base64", "", arg)
    assert expr.type_of() == pt.TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(actual.ops[0].expr, pt.Op.byte, "base64()"),
            pt.TealOp(actual.ops[1].expr, pt.Op.pop),
            pt.TealOp(arg, pt.Op.int, 1),
        ]
    )

    assert actual == expected


def test_nonce_base16():
    arg = pt.Int(1)
    expr = pt.Nonce("base16", "A21212EF", arg)
    assert expr.type_of() == pt.TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(actual.ops[0].expr, pt.Op.byte, "0xA21212EF"),
            pt.TealOp(actual.ops[1].expr, pt.Op.pop),
            pt.TealOp(arg, pt.Op.int, 1),
        ]
    )

    assert actual == expected


def test_nonce_base16_prefix():
    arg = pt.Int(1)
    expr = pt.Nonce("base16", "0xA21212EF", arg)
    assert expr.type_of() == pt.TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(actual.ops[0].expr, pt.Op.byte, "0xA21212EF"),
            pt.TealOp(actual.ops[1].expr, pt.Op.pop),
            pt.TealOp(arg, pt.Op.int, 1),
        ]
    )

    assert actual == expected


def test_nonce_base16_empty():
    arg = pt.Int(6)
    expr = pt.Nonce("base16", "", arg)
    assert expr.type_of() == pt.TealType.uint64

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    # copying expr from actual.ops[0] and actual.ops[1] because they can't be determined from outside code.
    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(actual.ops[0].expr, pt.Op.byte, "0x"),
            pt.TealOp(actual.ops[1].expr, pt.Op.pop),
            pt.TealOp(arg, pt.Op.int, 6),
        ]
    )

    assert actual == expected


def test_nonce_invalid():
    with pytest.raises(pt.TealInputError):
        pt.Nonce("base23", "", pt.Int(1))

    with pytest.raises(pt.TealInputError):
        pt.Nonce("base32", "Zm9vYmE=", pt.Int(1))

    with pytest.raises(pt.TealInputError):
        pt.Nonce("base64", "?????", pt.Int(1))

    with pytest.raises(pt.TealInputError):
        pt.Nonce(
            "base16",
            "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M",
            pt.Int(1),
        )
