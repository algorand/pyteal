import pytest

import pyteal as pt
from pyteal.errors import TealInputError

options = pt.CompileOptions()


def test_bytes_base32_no_padding():
    for s in (
        "ME",
        "MFRA",
        "MFRGG",
        "MFRGGZA",
        "MFRGGZDF",
        "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M",
    ):
        expr = pt.Bytes("base32", s)
        assert expr.type_of() == pt.TealType.bytes
        expected = pt.TealSimpleBlock(
            [pt.TealOp(expr, pt.Op.byte, "base32(" + s + ")")]
        )
        actual, _ = expr.__teal__(options)
        assert actual == expected


def test_bytes_base32_padding():
    for s in (
        "ME======",
        "MFRA====",
        "MFRGG===",
        "MFRGGZA=",
        "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M======",
    ):
        expr = pt.Bytes("base32", s)
        assert expr.type_of() == pt.TealType.bytes
        expected = pt.TealSimpleBlock(
            [pt.TealOp(expr, pt.Op.byte, "base32(" + s + ")")]
        )
        actual, _ = expr.__teal__(options)
        assert actual == expected


def test_bytes_base32_empty():
    expr = pt.Bytes("base32", "")
    assert expr.type_of() == pt.TealType.bytes
    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.byte, "base32()")])
    actual, _ = expr.__teal__(options)
    assert actual == expected


def test_bytes_base64():
    expr = pt.Bytes("base64", "Zm9vYmE=")
    assert expr.type_of() == pt.TealType.bytes
    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.byte, "base64(Zm9vYmE=)")])
    actual, _ = expr.__teal__(options)
    assert actual == expected


def test_bytes_base64_empty():
    expr = pt.Bytes("base64", "")
    assert expr.type_of() == pt.TealType.bytes
    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.byte, "base64()")])
    actual, _ = expr.__teal__(options)
    assert actual == expected


def test_bytes_base16():
    expr = pt.Bytes("base16", "A21212EF")
    assert expr.type_of() == pt.TealType.bytes
    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.byte, "0xA21212EF")])
    actual, _ = expr.__teal__(options)
    assert actual == expected


def test_bytes_base16_prefix():
    expr = pt.Bytes("base16", "0xA21212EF")
    assert expr.type_of() == pt.TealType.bytes
    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.byte, "0xA21212EF")])
    actual, _ = expr.__teal__(options)
    assert actual == expected


def test_bytes_base16_empty():
    expr = pt.Bytes("base16", "")
    assert expr.type_of() == pt.TealType.bytes
    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.byte, "0x")])
    actual, _ = expr.__teal__(options)
    assert actual == expected


B16_ODD_LEN_TESTCASES = ["F", "0c1"]


@pytest.mark.parametrize("testcase", B16_ODD_LEN_TESTCASES)
def test_bytes_base16_odd_len(testcase):
    with pytest.raises(TealInputError):
        pt.Bytes("base16", testcase)


def test_bytes_utf8():
    expr = pt.Bytes("hello world")
    assert expr.type_of() == pt.TealType.bytes
    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.byte, '"hello world"')])
    actual, _ = expr.__teal__(options)
    assert actual == expected


def test_bytes_utf8_special_chars():
    expr = pt.Bytes("\t \n \r\n \\ \" ' 😀")
    assert expr.type_of() == pt.TealType.bytes
    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(
                expr, pt.Op.byte, '"\\t \\n \\r\\n \\\\ \\" \' \\xf0\\x9f\\x98\\x80"'
            )
        ]
    )
    actual, _ = expr.__teal__(options)
    assert actual == expected


def test_bytes_utf8_empty():
    expr = pt.Bytes("")
    assert expr.type_of() == pt.TealType.bytes
    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.byte, '""')])
    actual, _ = expr.__teal__(options)
    assert actual == expected


def test_bytes_raw():
    for value in (b"hello world", bytearray(b"hello world")):
        expr = pt.Bytes(value)
        assert expr.type_of() == pt.TealType.bytes
        expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.byte, "0x" + value.hex())])
        actual, _ = expr.__teal__(options)
        assert actual == expected


def test_bytes_raw_empty():
    for value in (b"", bytearray(b"")):
        expr = pt.Bytes(value)
        assert expr.type_of() == pt.TealType.bytes
        expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.byte, "0x")])
        actual, _ = expr.__teal__(options)
        assert actual == expected


def test_bytes_invalid():
    with pytest.raises(pt.TealInputError):
        pt.Bytes("base16", b"FF")

    with pytest.raises(pt.TealInputError):
        pt.Bytes(b"base16", "FF")

    with pytest.raises(pt.TealInputError):
        pt.Bytes("base23", "")

    with pytest.raises(pt.TealInputError):
        pt.Bytes("base32", "Zm9vYmE=")

    with pytest.raises(pt.TealInputError):
        pt.Bytes("base32", "MFRGG====")

    with pytest.raises(pt.TealInputError):
        pt.Bytes("base32", "MFRGG==")

    with pytest.raises(pt.TealInputError):
        pt.Bytes("base32", "CCCCCC==")

    with pytest.raises(pt.TealInputError):
        pt.Bytes("base32", "CCCCCC")

    with pytest.raises(pt.TealInputError):
        pt.Bytes("base32", "C=======")

    with pytest.raises(pt.TealInputError):
        pt.Bytes("base32", "C")

    with pytest.raises(pt.TealInputError):
        pt.Bytes("base32", "=")

    with pytest.raises(pt.TealInputError):
        pt.Bytes("base64", "?????")

    with pytest.raises(pt.TealInputError):
        pt.Bytes("base16", "7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M")
