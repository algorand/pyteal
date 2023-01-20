import pytest

import pyteal as pt

avm2Options = pt.CompileOptions(version=2)
avm3Options = pt.CompileOptions(version=3)
avm4Options = pt.CompileOptions(version=4)
avm5Options = pt.CompileOptions(version=5)
avm6Options = pt.CompileOptions(version=6)
avm7Options = pt.CompileOptions(version=7)


def test_ed25519verify():
    args = [pt.Bytes("data"), pt.Bytes("sig"), pt.Bytes("key")]
    expr = pt.Ed25519Verify(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"data"'),
            pt.TealOp(args[1], pt.Op.byte, '"sig"'),
            pt.TealOp(args[2], pt.Op.byte, '"key"'),
            pt.TealOp(expr, pt.Op.ed25519verify),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_ed25519verify_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Ed25519Verify(pt.Int(0), pt.Bytes("sig"), pt.Bytes("key"))

    with pytest.raises(pt.TealTypeError):
        pt.Ed25519Verify(pt.Bytes("data"), pt.Int(0), pt.Bytes("key"))

    with pytest.raises(pt.TealTypeError):
        pt.Ed25519Verify(pt.Bytes("data"), pt.Bytes("sig"), pt.Int(0))


def test_ed25519verify_bare():
    args = [pt.Bytes("data"), pt.Bytes("sig"), pt.Bytes("key")]
    expr = pt.Ed25519Verify_Bare(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"data"'),
            pt.TealOp(args[1], pt.Op.byte, '"sig"'),
            pt.TealOp(args[2], pt.Op.byte, '"key"'),
            pt.TealOp(expr, pt.Op.ed25519verify_bare),
        ]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm6Options)


def test_ed25519verify_bare_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Ed25519Verify_Bare(pt.Int(0), pt.Bytes("sig"), pt.Bytes("key"))

    with pytest.raises(pt.TealTypeError):
        pt.Ed25519Verify_Bare(pt.Bytes("data"), pt.Int(0), pt.Bytes("key"))

    with pytest.raises(pt.TealTypeError):
        pt.Ed25519Verify_Bare(pt.Bytes("data"), pt.Bytes("sig"), pt.Int(0))


def test_set_bit_int():
    args = [pt.Int(0), pt.Int(2), pt.Int(1)]
    expr = pt.SetBit(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, 0),
            pt.TealOp(args[1], pt.Op.int, 2),
            pt.TealOp(args[2], pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.setbit),
        ]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm2Options)


def test_set_bit_bytes():
    args = [pt.Bytes("base16", "0x0000"), pt.Int(0), pt.Int(1)]
    expr = pt.SetBit(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0x0000"),
            pt.TealOp(args[1], pt.Op.int, 0),
            pt.TealOp(args[2], pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.setbit),
        ]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm2Options)


def test_set_bit_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.SetBit(pt.Int(3), pt.Bytes("index"), pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        pt.SetBit(pt.Int(3), pt.Int(0), pt.Bytes("one"))

    with pytest.raises(pt.TealTypeError):
        pt.SetBit(pt.Bytes("base16", "0xFF"), pt.Bytes("index"), pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        pt.SetBit(pt.Bytes("base16", "0xFF"), pt.Int(0), pt.Bytes("one"))


def test_set_byte():
    args = [pt.Bytes("base16", "0xFF"), pt.Int(0), pt.Int(3)]
    expr = pt.SetByte(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, "0xFF"),
            pt.TealOp(args[1], pt.Op.int, 0),
            pt.TealOp(args[2], pt.Op.int, 3),
            pt.TealOp(expr, pt.Op.setbyte),
        ]
    )

    actual, _ = expr.__teal__(avm3Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm2Options)


def test_set_byte_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.SetByte(pt.Int(3), pt.Int(0), pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        pt.SetByte(pt.Bytes("base16", "0xFF"), pt.Bytes("index"), pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        pt.SetByte(pt.Bytes("base16", "0xFF"), pt.Int(0), pt.Bytes("one"))


def test_divw():
    args = [pt.Int(0), pt.Int(90), pt.Int(30)]
    expr = pt.Divw(args[0], args[1], args[2])
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.int, args[0].value),
            pt.TealOp(args[1], pt.Op.int, args[1].value),
            pt.TealOp(args[2], pt.Op.int, args[2].value),
            pt.TealOp(expr, pt.Op.divw),
        ]
    )

    actual, _ = expr.__teal__(avm6Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_divw_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Divw(pt.Bytes("10"), pt.Int(0), pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        pt.Divw(pt.Int(10), pt.Bytes("0"), pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        pt.Divw(pt.Int(10), pt.Int(0), pt.Bytes("1"))
