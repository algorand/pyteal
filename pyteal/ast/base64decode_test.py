import pytest

import pyteal as pt

avm6Options = pt.CompileOptions(version=6)
avm7Options = pt.CompileOptions(version=7)


def test_base64decode_std():
    arg = pt.Bytes("aGVsbG8gd29ybGQ=")
    expr = pt.Base64Decode.std(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.byte, '"aGVsbG8gd29ybGQ="'),
            pt.TealOp(expr, pt.Op.base64_decode, "StdEncoding"),
        ]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm6Options)


def test_base64decode_url():
    arg = pt.Bytes("aGVsbG8gd29ybGQ")
    expr = pt.Base64Decode.url(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.byte, '"aGVsbG8gd29ybGQ"'),
            pt.TealOp(expr, pt.Op.base64_decode, "URLEncoding"),
        ]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm6Options)


def test_base64decode_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Base64Decode.std(pt.Int(0))
    with pytest.raises(pt.TealTypeError):
        pt.Base64Decode.url(pt.Int(0))
