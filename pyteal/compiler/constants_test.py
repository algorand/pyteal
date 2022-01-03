from .. import *

from .constants import (
    extractIntValue,
    extractBytesValue,
    extractAddrValue,
    createConstantBlocks,
    extractMethodSigValue,
)


def test_extractIntValue():
    tests = [
        (TealOp(None, Op.int, 0), 0),
        (TealOp(None, Op.int, 5), 5),
        (TealOp(None, Op.int, "pay"), 1),
        (TealOp(None, Op.int, "NoOp"), 0),
        (TealOp(None, Op.int, "UpdateApplication"), 4),
        (TealOp(None, Op.int, "TMPL_NAME"), "TMPL_NAME"),
    ]

    for op, expected in tests:
        actual = extractIntValue(op)
        assert actual == expected


def test_extractBytesValue():
    tests = [
        (TealOp(None, Op.byte, '""'), b""),
        (TealOp(None, Op.byte, '"test"'), b"test"),
        (TealOp(None, Op.byte, '"\\t\\n\\\\\\""'), b'\t\n\\"'),
        (TealOp(None, Op.byte, "0x"), b""),
        (TealOp(None, Op.byte, "0x00"), b"\x00"),
        (TealOp(None, Op.byte, "0xFF00"), b"\xff\x00"),
        (TealOp(None, Op.byte, "0xff00"), b"\xff\x00"),
        (TealOp(None, Op.byte, "base32()"), b""),
        (TealOp(None, Op.byte, "base32(ORSXG5A)"), b"test"),
        (TealOp(None, Op.byte, "base32(ORSXG5A=)"), b"test"),
        (TealOp(None, Op.byte, "base64()"), b""),
        (TealOp(None, Op.byte, "base64(dGVzdA==)"), b"test"),
        (TealOp(None, Op.byte, "TMPL_NAME"), "TMPL_NAME"),
    ]

    for op, expected in tests:
        actual = extractBytesValue(op)
        assert actual == expected


def test_extractAddrValue():
    tests = [
        (
            TealOp(
                None,
                Op.byte,
                "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M",
            ),
            b"\xb4\x92v\xbd>\xc0\x97~\xab\x86\xa3!\xc4I\xea\xd8\x02\xc9l\x0b\xd9|)V\x13\x15\x11\xd2\xf1\x1e\xeb\xec",
        ),
        (TealOp(None, Op.addr, "TMPL_NAME"), "TMPL_NAME"),
    ]

    for op, expected in tests:
        actual = extractAddrValue(op)
        assert actual == expected


# test case came from: https://gist.github.com/jasonpaulos/99e4f8a75f2fc2ec9b8073c064530359
def test_extractMethodValue():
    tests = [
        (
            TealOp(None, Op.method_signature, '"create(uint64)uint64"'),
            b"\x43\x46\x41\x01",
        ),
        (TealOp(None, Op.method_signature, '"update()void"'), b"\xa0\xe8\x18\x72"),
        (
            TealOp(None, Op.method_signature, '"optIn(string)string"'),
            b"\xcf\xa6\x8e\x36",
        ),
        (TealOp(None, Op.method_signature, '"closeOut()string"'), b"\xa9\xf4\x2b\x3d"),
        (TealOp(None, Op.method_signature, '"delete()void"'), b"\x24\x37\x8d\x3c"),
        (
            TealOp(None, Op.method_signature, '"add(uint64,uint64)uint64"'),
            b"\xfe\x6b\xdf\x69",
        ),
        (TealOp(None, Op.method_signature, '"empty()void"'), b"\xa8\x8c\x26\xa5"),
        (
            TealOp(None, Op.method_signature, '"payment(pay,uint64)bool"'),
            b"\x3e\x3b\x3d\x28",
        ),
        (
            TealOp(
                None,
                Op.method_signature,
                '"referenceTest(account,application,account,asset,account,asset,asset,application,application)uint8[9]"',
            ),
            b"\x0d\xf0\x05\x0f",
        ),
    ]

    for op, expected in tests:
        actual = extractMethodSigValue(op)
        assert actual == expected


def test_createConstantBlocks_empty():
    ops = []

    expected = ops[:]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_no_consts():
    ops = [
        TealOp(None, Op.txn, "Sender"),
        TealOp(None, Op.txn, "Receiver"),
        TealOp(None, Op.eq),
    ]

    expected = ops[:]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_pushint():
    ops = [
        TealOp(None, Op.int, 0),
        TealOp(None, Op.int, "OptIn"),
        TealOp(None, Op.add),
    ]

    expected = [
        TealOp(None, Op.pushint, 0, "//", 0),
        TealOp(None, Op.pushint, 1, "//", "OptIn"),
        TealOp(None, Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_intblock_single():
    ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, "OptIn"),
        TealOp(None, Op.add),
    ]

    expected = [
        TealOp(None, Op.intcblock, 1),
        TealOp(None, Op.intc_0, "//", 1),
        TealOp(None, Op.intc_0, "//", "OptIn"),
        TealOp(None, Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_intblock_multiple():
    ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, "OptIn"),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, "keyreg"),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.int, "ClearState"),
        TealOp(None, Op.add),
    ]

    expected = [
        TealOp(None, Op.intcblock, 1, 2, 3),
        TealOp(None, Op.intc_0, "//", 1),
        TealOp(None, Op.intc_0, "//", "OptIn"),
        TealOp(None, Op.add),
        TealOp(None, Op.intc_1, "//", 2),
        TealOp(None, Op.intc_1, "//", "keyreg"),
        TealOp(None, Op.add),
        TealOp(None, Op.intc_2, "//", 3),
        TealOp(None, Op.intc_2, "//", "ClearState"),
        TealOp(None, Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_intblock_pushint():
    ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, "OptIn"),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.int, "ClearState"),
        TealOp(None, Op.add),
    ]

    expected = [
        TealOp(None, Op.intcblock, 3, 1),
        TealOp(None, Op.intc_1, "//", 1),
        TealOp(None, Op.intc_1, "//", "OptIn"),
        TealOp(None, Op.add),
        TealOp(None, Op.pushint, 2, "//", 2),
        TealOp(None, Op.intc_0, "//", 3),
        TealOp(None, Op.add),
        TealOp(None, Op.intc_0, "//", 3),
        TealOp(None, Op.intc_0, "//", "ClearState"),
        TealOp(None, Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_pushbytes():
    ops = [
        TealOp(None, Op.byte, "0x0102"),
        TealOp(None, Op.byte, "0x0103"),
        TealOp(None, Op.method_signature, '"empty()void"'),
        TealOp(None, Op.concat),
    ]

    expected = [
        TealOp(None, Op.pushbytes, "0x0102", "//", "0x0102"),
        TealOp(None, Op.pushbytes, "0x0103", "//", "0x0103"),
        TealOp(None, Op.pushbytes, "0xa88c26a5", "//", '"empty()void"'),
        TealOp(None, Op.concat),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_byteblock_single():
    ops = [
        TealOp(None, Op.byte, "0x0102"),
        TealOp(None, Op.byte, "base64(AQI=)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "base32(AEBA====)"),
        TealOp(None, Op.concat),
    ]

    expected = [
        TealOp(None, Op.bytecblock, "0x0102"),
        TealOp(None, Op.bytec_0, "//", "0x0102"),
        TealOp(None, Op.bytec_0, "//", "base64(AQI=)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_0, "//", "base32(AEBA====)"),
        TealOp(None, Op.concat),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_byteblock_multiple():
    ops = [
        TealOp(None, Op.byte, "0x0102"),
        TealOp(None, Op.byte, "base64(AQI=)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "base32(AEBA====)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, '"test"'),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "base32(ORSXG5A=)"),
        TealOp(None, Op.concat),
        TealOp(
            None,
            Op.byte,
            "0xb49276bd3ec0977eab86a321c449ead802c96c0bd97c2956131511d2f11eebec",
        ),
        TealOp(None, Op.concat),
        TealOp(
            None, Op.addr, "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M"
        ),
        TealOp(None, Op.concat),
        TealOp(None, Op.method_signature, '"closeOut()string"'),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "base64(qfQrPQ==)"),
    ]

    expected = [
        TealOp(
            None,
            Op.bytecblock,
            "0x0102",
            "0x74657374",
            "0xb49276bd3ec0977eab86a321c449ead802c96c0bd97c2956131511d2f11eebec",
            "0xa9f42b3d",
        ),
        TealOp(None, Op.bytec_0, "//", "0x0102"),
        TealOp(None, Op.bytec_0, "//", "base64(AQI=)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_0, "//", "base32(AEBA====)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_1, "//", '"test"'),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_1, "//", "base32(ORSXG5A=)"),
        TealOp(None, Op.concat),
        TealOp(
            None,
            Op.bytec_2,
            "//",
            "0xb49276bd3ec0977eab86a321c449ead802c96c0bd97c2956131511d2f11eebec",
        ),
        TealOp(None, Op.concat),
        TealOp(
            None,
            Op.bytec_2,
            "//",
            "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M",
        ),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_3, "//", '"closeOut()string"'),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_3, "//", "base64(qfQrPQ==)"),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_byteblock_pushbytes():
    ops = [
        TealOp(None, Op.byte, "0x0102"),
        TealOp(None, Op.byte, "base64(AQI=)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "base32(AEBA====)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, '"test"'),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "base32(ORSXG5A=)"),
        TealOp(None, Op.concat),
        TealOp(
            None, Op.addr, "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M"
        ),
        TealOp(None, Op.concat),
    ]

    expected = [
        TealOp(None, Op.bytecblock, "0x0102", "0x74657374"),
        TealOp(None, Op.bytec_0, "//", "0x0102"),
        TealOp(None, Op.bytec_0, "//", "base64(AQI=)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_0, "//", "base32(AEBA====)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_1, "//", '"test"'),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_1, "//", "base32(ORSXG5A=)"),
        TealOp(None, Op.concat),
        TealOp(
            None,
            Op.pushbytes,
            "0xb49276bd3ec0977eab86a321c449ead802c96c0bd97c2956131511d2f11eebec",
            "//",
            "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M",
        ),
        TealOp(None, Op.concat),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_all():
    ops = [
        TealOp(None, Op.byte, "0x0102"),
        TealOp(None, Op.byte, "base64(AQI=)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "base32(AEBA====)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, '"test"'),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "base32(ORSXG5A=)"),
        TealOp(None, Op.concat),
        TealOp(
            None, Op.addr, "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M"
        ),
        TealOp(None, Op.concat),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, "OptIn"),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.int, "ClearState"),
        TealOp(None, Op.add),
    ]

    expected = [
        TealOp(None, Op.intcblock, 3, 1),
        TealOp(None, Op.bytecblock, "0x0102", "0x74657374"),
        TealOp(None, Op.bytec_0, "//", "0x0102"),
        TealOp(None, Op.bytec_0, "//", "base64(AQI=)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_0, "//", "base32(AEBA====)"),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_1, "//", '"test"'),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_1, "//", "base32(ORSXG5A=)"),
        TealOp(None, Op.concat),
        TealOp(
            None,
            Op.pushbytes,
            "0xb49276bd3ec0977eab86a321c449ead802c96c0bd97c2956131511d2f11eebec",
            "//",
            "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M",
        ),
        TealOp(None, Op.concat),
        TealOp(None, Op.intc_1, "//", 1),
        TealOp(None, Op.intc_1, "//", "OptIn"),
        TealOp(None, Op.add),
        TealOp(None, Op.pushint, 2, "//", 2),
        TealOp(None, Op.intc_0, "//", 3),
        TealOp(None, Op.add),
        TealOp(None, Op.intc_0, "//", 3),
        TealOp(None, Op.intc_0, "//", "ClearState"),
        TealOp(None, Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_tmpl_int():
    ops = [
        TealOp(None, Op.int, "TMPL_INT_1"),
        TealOp(None, Op.int, "TMPL_INT_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.int, "TMPL_INT_2"),
        TealOp(None, Op.add),
    ]

    expected = [
        TealOp(None, Op.intcblock, "TMPL_INT_1"),
        TealOp(None, Op.intc_0, "//", "TMPL_INT_1"),
        TealOp(None, Op.intc_0, "//", "TMPL_INT_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.pushint, "TMPL_INT_2", "//", "TMPL_INT_2"),
        TealOp(None, Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_tmpl_int_mixed():
    ops = [
        TealOp(None, Op.int, "TMPL_INT_1"),
        TealOp(None, Op.int, "TMPL_INT_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.int, "TMPL_INT_2"),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
    ]

    expected = [
        TealOp(None, Op.intcblock, "TMPL_INT_1", 0),
        TealOp(None, Op.intc_0, "//", "TMPL_INT_1"),
        TealOp(None, Op.intc_0, "//", "TMPL_INT_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.pushint, "TMPL_INT_2", "//", "TMPL_INT_2"),
        TealOp(None, Op.add),
        TealOp(None, Op.intc_1, "//", 0),
        TealOp(None, Op.intc_1, "//", 0),
        TealOp(None, Op.add),
        TealOp(None, Op.pushint, 1, "//", 1),
        TealOp(None, Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_tmpl_bytes():
    ops = [
        TealOp(None, Op.byte, "TMPL_BYTES_1"),
        TealOp(None, Op.byte, "TMPL_BYTES_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.byte, "TMPL_BYTES_2"),
        TealOp(None, Op.concat),
    ]

    expected = [
        TealOp(None, Op.bytecblock, "TMPL_BYTES_1"),
        TealOp(None, Op.bytec_0, "//", "TMPL_BYTES_1"),
        TealOp(None, Op.bytec_0, "//", "TMPL_BYTES_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.pushbytes, "TMPL_BYTES_2", "//", "TMPL_BYTES_2"),
        TealOp(None, Op.concat),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_tmpl_bytes_mixed():
    ops = [
        TealOp(None, Op.byte, "TMPL_BYTES_1"),
        TealOp(None, Op.byte, "TMPL_BYTES_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.byte, "TMPL_BYTES_2"),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "0x01"),
        TealOp(None, Op.concat),
    ]

    expected = [
        TealOp(None, Op.bytecblock, "TMPL_BYTES_1", "0x00"),
        TealOp(None, Op.bytec_0, "//", "TMPL_BYTES_1"),
        TealOp(None, Op.bytec_0, "//", "TMPL_BYTES_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.pushbytes, "TMPL_BYTES_2", "//", "TMPL_BYTES_2"),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_1, "//", "0x00"),
        TealOp(None, Op.bytec_1, "//", "0x00"),
        TealOp(None, Op.concat),
        TealOp(None, Op.pushbytes, "0x01", "//", "0x01"),
        TealOp(None, Op.concat),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_tmpl_all():
    ops = [
        TealOp(None, Op.byte, "TMPL_BYTES_1"),
        TealOp(None, Op.byte, "TMPL_BYTES_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.byte, "TMPL_BYTES_2"),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.byte, "0x00"),
        TealOp(None, Op.concat),
        TealOp(None, Op.byte, "0x01"),
        TealOp(None, Op.concat),
        TealOp(None, Op.len),
        TealOp(None, Op.int, "TMPL_INT_1"),
        TealOp(None, Op.int, "TMPL_INT_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.int, "TMPL_INT_2"),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.add),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.eq),
    ]

    expected = [
        TealOp(None, Op.intcblock, "TMPL_INT_1", 0),
        TealOp(None, Op.bytecblock, "TMPL_BYTES_1", "0x00"),
        TealOp(None, Op.bytec_0, "//", "TMPL_BYTES_1"),
        TealOp(None, Op.bytec_0, "//", "TMPL_BYTES_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.pushbytes, "TMPL_BYTES_2", "//", "TMPL_BYTES_2"),
        TealOp(None, Op.concat),
        TealOp(None, Op.bytec_1, "//", "0x00"),
        TealOp(None, Op.bytec_1, "//", "0x00"),
        TealOp(None, Op.concat),
        TealOp(None, Op.pushbytes, "0x01", "//", "0x01"),
        TealOp(None, Op.concat),
        TealOp(None, Op.len),
        TealOp(None, Op.intc_0, "//", "TMPL_INT_1"),
        TealOp(None, Op.intc_0, "//", "TMPL_INT_1"),
        TealOp(None, Op.eq),
        TealOp(None, Op.pushint, "TMPL_INT_2", "//", "TMPL_INT_2"),
        TealOp(None, Op.add),
        TealOp(None, Op.intc_1, "//", 0),
        TealOp(None, Op.intc_1, "//", 0),
        TealOp(None, Op.add),
        TealOp(None, Op.pushint, 1, "//", 1),
        TealOp(None, Op.add),
        TealOp(None, Op.eq),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_intc():
    """Test scenario where there are more than 4 constants in the intcblock.
    If the 4th constant can't fit in one varuint byte (more than 2**7) it
    should be referenced with the Op.intc 4 command.
    """

    ops = [
        TealOp(None, Op.int, 0),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.int, 2 ** 7),
        TealOp(None, Op.int, 2 ** 7),
    ]

    expected = [
        TealOp(None, Op.intcblock, 0, 1, 2, 3, 2 ** 7),
        TealOp(None, Op.intc_0, "//", 0),
        TealOp(None, Op.intc_0, "//", 0),
        TealOp(None, Op.intc_1, "//", 1),
        TealOp(None, Op.intc_1, "//", 1),
        TealOp(None, Op.intc_2, "//", 2),
        TealOp(None, Op.intc_2, "//", 2),
        TealOp(None, Op.intc_3, "//", 3),
        TealOp(None, Op.intc_3, "//", 3),
        TealOp(None, Op.intc, 4, "//", 2 ** 7),
        TealOp(None, Op.intc, 4, "//", 2 ** 7),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_small_constant():
    """If a constant cannot be referenced using the intc_[0..3] commands
    and it can be stored in one varuint it byte then Op.pushint is used.
    """

    for cur in range(4, 2 ** 7):
        ops = [
            TealOp(None, Op.int, 0),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.int, cur),
            TealOp(None, Op.int, cur),
        ]

        expected = [
            TealOp(None, Op.intcblock, 0, 1, 2, 3),
            TealOp(None, Op.intc_0, "//", 0),
            TealOp(None, Op.intc_0, "//", 0),
            TealOp(None, Op.intc_1, "//", 1),
            TealOp(None, Op.intc_1, "//", 1),
            TealOp(None, Op.intc_2, "//", 2),
            TealOp(None, Op.intc_2, "//", 2),
            TealOp(None, Op.intc_3, "//", 3),
            TealOp(None, Op.intc_3, "//", 3),
            TealOp(None, Op.pushint, cur, "//", cur),
            TealOp(None, Op.pushint, cur, "//", cur),
        ]

        actual = createConstantBlocks(ops)
        assert actual == expected
