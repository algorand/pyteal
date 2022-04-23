import pyteal as pt

from pyteal.compiler.constants import (
    extractIntValue,
    extractBytesValue,
    extractAddrValue,
    createConstantBlocks,
    extractMethodSigValue,
)


def test_extractIntValue():
    tests = [
        (pt.TealOp(None, pt.Op.int, 0), 0),
        (pt.TealOp(None, pt.Op.int, 5), 5),
        (pt.TealOp(None, pt.Op.int, "pay"), 1),
        (pt.TealOp(None, pt.Op.int, "NoOp"), 0),
        (pt.TealOp(None, pt.Op.int, "UpdateApplication"), 4),
        (pt.TealOp(None, pt.Op.int, "TMPL_NAME"), "TMPL_NAME"),
    ]

    for op, expected in tests:
        actual = extractIntValue(op)
        assert actual == expected


def test_extractBytesValue():
    tests = [
        (pt.TealOp(None, pt.Op.byte, '""'), b""),
        (pt.TealOp(None, pt.Op.byte, '"test"'), b"test"),
        (pt.TealOp(None, pt.Op.byte, '"\\t\\n\\\\\\""'), b'\t\n\\"'),
        (pt.TealOp(None, pt.Op.byte, "0x"), b""),
        (pt.TealOp(None, pt.Op.byte, "0x00"), b"\x00"),
        (pt.TealOp(None, pt.Op.byte, "0xFF00"), b"\xff\x00"),
        (pt.TealOp(None, pt.Op.byte, "0xff00"), b"\xff\x00"),
        (pt.TealOp(None, pt.Op.byte, "base32()"), b""),
        (pt.TealOp(None, pt.Op.byte, "base32(ORSXG5A)"), b"test"),
        (pt.TealOp(None, pt.Op.byte, "base32(ORSXG5A=)"), b"test"),
        (pt.TealOp(None, pt.Op.byte, "base64()"), b""),
        (pt.TealOp(None, pt.Op.byte, "base64(dGVzdA==)"), b"test"),
        (pt.TealOp(None, pt.Op.byte, "TMPL_NAME"), "TMPL_NAME"),
    ]

    for op, expected in tests:
        actual = extractBytesValue(op)
        assert actual == expected


def test_extractAddrValue():
    tests = [
        (
            pt.TealOp(
                None,
                pt.Op.byte,
                "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M",
            ),
            b"\xb4\x92v\xbd>\xc0\x97~\xab\x86\xa3!\xc4I\xea\xd8\x02\xc9l\x0b\xd9|)V\x13\x15\x11\xd2\xf1\x1e\xeb\xec",
        ),
        (pt.TealOp(None, pt.Op.addr, "TMPL_NAME"), "TMPL_NAME"),
    ]

    for op, expected in tests:
        actual = extractAddrValue(op)
        assert actual == expected


# test case came from: https://gist.github.com/jasonpaulos/99e4f8a75f2fc2ec9b8073c064530359
def test_extractMethodValue():
    tests = [
        (
            pt.TealOp(None, pt.Op.method_signature, '"create(uint64)uint64"'),
            b"\x43\x46\x41\x01",
        ),
        (
            pt.TealOp(None, pt.Op.method_signature, '"update()void"'),
            b"\xa0\xe8\x18\x72",
        ),
        (
            pt.TealOp(None, pt.Op.method_signature, '"optIn(string)string"'),
            b"\xcf\xa6\x8e\x36",
        ),
        (
            pt.TealOp(None, pt.Op.method_signature, '"closeOut()string"'),
            b"\xa9\xf4\x2b\x3d",
        ),
        (
            pt.TealOp(None, pt.Op.method_signature, '"delete()void"'),
            b"\x24\x37\x8d\x3c",
        ),
        (
            pt.TealOp(None, pt.Op.method_signature, '"add(uint64,uint64)uint64"'),
            b"\xfe\x6b\xdf\x69",
        ),
        (pt.TealOp(None, pt.Op.method_signature, '"empty()void"'), b"\xa8\x8c\x26\xa5"),
        (
            pt.TealOp(None, pt.Op.method_signature, '"payment(pay,uint64)bool"'),
            b"\x3e\x3b\x3d\x28",
        ),
        (
            pt.TealOp(
                None,
                pt.Op.method_signature,
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
        pt.TealOp(None, pt.Op.txn, "Sender"),
        pt.TealOp(None, pt.Op.txn, "Receiver"),
        pt.TealOp(None, pt.Op.eq),
    ]

    expected = ops[:]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_pushint():
    ops = [
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.int, "OptIn"),
        pt.TealOp(None, pt.Op.add),
    ]

    expected = [
        pt.TealOp(None, pt.Op.pushint, 0, "//", 0),
        pt.TealOp(None, pt.Op.pushint, 1, "//", "OptIn"),
        pt.TealOp(None, pt.Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_intblock_single():
    ops = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, "OptIn"),
        pt.TealOp(None, pt.Op.add),
    ]

    expected = [
        pt.TealOp(None, pt.Op.intcblock, 1),
        pt.TealOp(None, pt.Op.intc_0, "//", 1),
        pt.TealOp(None, pt.Op.intc_0, "//", "OptIn"),
        pt.TealOp(None, pt.Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_intblock_multiple():
    ops = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, "OptIn"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, "keyreg"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.int, "ClearState"),
        pt.TealOp(None, pt.Op.add),
    ]

    expected = [
        pt.TealOp(None, pt.Op.intcblock, 1, 2, 3),
        pt.TealOp(None, pt.Op.intc_0, "//", 1),
        pt.TealOp(None, pt.Op.intc_0, "//", "OptIn"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.intc_1, "//", 2),
        pt.TealOp(None, pt.Op.intc_1, "//", "keyreg"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.intc_2, "//", 3),
        pt.TealOp(None, pt.Op.intc_2, "//", "ClearState"),
        pt.TealOp(None, pt.Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_intblock_pushint():
    ops = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, "OptIn"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.int, "ClearState"),
        pt.TealOp(None, pt.Op.add),
    ]

    expected = [
        pt.TealOp(None, pt.Op.intcblock, 3, 1),
        pt.TealOp(None, pt.Op.intc_1, "//", 1),
        pt.TealOp(None, pt.Op.intc_1, "//", "OptIn"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.pushint, 2, "//", 2),
        pt.TealOp(None, pt.Op.intc_0, "//", 3),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.intc_0, "//", 3),
        pt.TealOp(None, pt.Op.intc_0, "//", "ClearState"),
        pt.TealOp(None, pt.Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_pushbytes():
    ops = [
        pt.TealOp(None, pt.Op.byte, "0x0102"),
        pt.TealOp(None, pt.Op.byte, "0x0103"),
        pt.TealOp(None, pt.Op.method_signature, '"empty()void"'),
        pt.TealOp(None, pt.Op.concat),
    ]

    expected = [
        pt.TealOp(None, pt.Op.pushbytes, "0x0102", "//", "0x0102"),
        pt.TealOp(None, pt.Op.pushbytes, "0x0103", "//", "0x0103"),
        pt.TealOp(None, pt.Op.pushbytes, "0xa88c26a5", "//", '"empty()void"'),
        pt.TealOp(None, pt.Op.concat),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_byteblock_single():
    ops = [
        pt.TealOp(None, pt.Op.byte, "0x0102"),
        pt.TealOp(None, pt.Op.byte, "base64(AQI=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "base32(AEBA====)"),
        pt.TealOp(None, pt.Op.concat),
    ]

    expected = [
        pt.TealOp(None, pt.Op.bytecblock, "0x0102"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "0x0102"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "base64(AQI=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_0, "//", "base32(AEBA====)"),
        pt.TealOp(None, pt.Op.concat),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_byteblock_multiple():
    ops = [
        pt.TealOp(None, pt.Op.byte, "0x0102"),
        pt.TealOp(None, pt.Op.byte, "base64(AQI=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "base32(AEBA====)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, '"test"'),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "base32(ORSXG5A=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(
            None,
            pt.Op.byte,
            "0xb49276bd3ec0977eab86a321c449ead802c96c0bd97c2956131511d2f11eebec",
        ),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(
            None,
            pt.Op.addr,
            "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M",
        ),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.method_signature, '"closeOut()string"'),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "base64(qfQrPQ==)"),
    ]

    expected = [
        pt.TealOp(
            None,
            pt.Op.bytecblock,
            "0x0102",
            "0x74657374",
            "0xb49276bd3ec0977eab86a321c449ead802c96c0bd97c2956131511d2f11eebec",
            "0xa9f42b3d",
        ),
        pt.TealOp(None, pt.Op.bytec_0, "//", "0x0102"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "base64(AQI=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_0, "//", "base32(AEBA====)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_1, "//", '"test"'),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_1, "//", "base32(ORSXG5A=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(
            None,
            pt.Op.bytec_2,
            "//",
            "0xb49276bd3ec0977eab86a321c449ead802c96c0bd97c2956131511d2f11eebec",
        ),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(
            None,
            pt.Op.bytec_2,
            "//",
            "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M",
        ),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_3, "//", '"closeOut()string"'),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_3, "//", "base64(qfQrPQ==)"),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_byteblock_pushbytes():
    ops = [
        pt.TealOp(None, pt.Op.byte, "0x0102"),
        pt.TealOp(None, pt.Op.byte, "base64(AQI=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "base32(AEBA====)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, '"test"'),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "base32(ORSXG5A=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(
            None,
            pt.Op.addr,
            "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M",
        ),
        pt.TealOp(None, pt.Op.concat),
    ]

    expected = [
        pt.TealOp(None, pt.Op.bytecblock, "0x0102", "0x74657374"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "0x0102"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "base64(AQI=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_0, "//", "base32(AEBA====)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_1, "//", '"test"'),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_1, "//", "base32(ORSXG5A=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(
            None,
            pt.Op.pushbytes,
            "0xb49276bd3ec0977eab86a321c449ead802c96c0bd97c2956131511d2f11eebec",
            "//",
            "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M",
        ),
        pt.TealOp(None, pt.Op.concat),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_all():
    ops = [
        pt.TealOp(None, pt.Op.byte, "0x0102"),
        pt.TealOp(None, pt.Op.byte, "base64(AQI=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "base32(AEBA====)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, '"test"'),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "base32(ORSXG5A=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(
            None,
            pt.Op.addr,
            "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M",
        ),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, "OptIn"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.int, "ClearState"),
        pt.TealOp(None, pt.Op.add),
    ]

    expected = [
        pt.TealOp(None, pt.Op.intcblock, 3, 1),
        pt.TealOp(None, pt.Op.bytecblock, "0x0102", "0x74657374"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "0x0102"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "base64(AQI=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_0, "//", "base32(AEBA====)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_1, "//", '"test"'),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_1, "//", "base32(ORSXG5A=)"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(
            None,
            pt.Op.pushbytes,
            "0xb49276bd3ec0977eab86a321c449ead802c96c0bd97c2956131511d2f11eebec",
            "//",
            "WSJHNPJ6YCLX5K4GUMQ4ISPK3ABMS3AL3F6CSVQTCUI5F4I65PWEMCWT3M",
        ),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.intc_1, "//", 1),
        pt.TealOp(None, pt.Op.intc_1, "//", "OptIn"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.pushint, 2, "//", 2),
        pt.TealOp(None, pt.Op.intc_0, "//", 3),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.intc_0, "//", 3),
        pt.TealOp(None, pt.Op.intc_0, "//", "ClearState"),
        pt.TealOp(None, pt.Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_tmpl_int():
    ops = [
        pt.TealOp(None, pt.Op.int, "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.int, "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.int, "TMPL_INT_2"),
        pt.TealOp(None, pt.Op.add),
    ]

    expected = [
        pt.TealOp(None, pt.Op.intcblock, "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.intc_0, "//", "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.intc_0, "//", "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.pushint, "TMPL_INT_2", "//", "TMPL_INT_2"),
        pt.TealOp(None, pt.Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_tmpl_int_mixed():
    ops = [
        pt.TealOp(None, pt.Op.int, "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.int, "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.int, "TMPL_INT_2"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
    ]

    expected = [
        pt.TealOp(None, pt.Op.intcblock, "TMPL_INT_1", 0),
        pt.TealOp(None, pt.Op.intc_0, "//", "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.intc_0, "//", "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.pushint, "TMPL_INT_2", "//", "TMPL_INT_2"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.intc_1, "//", 0),
        pt.TealOp(None, pt.Op.intc_1, "//", 0),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.pushint, 1, "//", 1),
        pt.TealOp(None, pt.Op.add),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_tmpl_bytes():
    ops = [
        pt.TealOp(None, pt.Op.byte, "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.byte, "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.byte, "TMPL_BYTES_2"),
        pt.TealOp(None, pt.Op.concat),
    ]

    expected = [
        pt.TealOp(None, pt.Op.bytecblock, "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.pushbytes, "TMPL_BYTES_2", "//", "TMPL_BYTES_2"),
        pt.TealOp(None, pt.Op.concat),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_tmpl_bytes_mixed():
    ops = [
        pt.TealOp(None, pt.Op.byte, "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.byte, "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.byte, "TMPL_BYTES_2"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "0x00"),
        pt.TealOp(None, pt.Op.byte, "0x00"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "0x01"),
        pt.TealOp(None, pt.Op.concat),
    ]

    expected = [
        pt.TealOp(None, pt.Op.bytecblock, "TMPL_BYTES_1", "0x00"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.pushbytes, "TMPL_BYTES_2", "//", "TMPL_BYTES_2"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_1, "//", "0x00"),
        pt.TealOp(None, pt.Op.bytec_1, "//", "0x00"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.pushbytes, "0x01", "//", "0x01"),
        pt.TealOp(None, pt.Op.concat),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_tmpl_all():
    ops = [
        pt.TealOp(None, pt.Op.byte, "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.byte, "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.byte, "TMPL_BYTES_2"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "0x00"),
        pt.TealOp(None, pt.Op.byte, "0x00"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.byte, "0x01"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.len),
        pt.TealOp(None, pt.Op.int, "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.int, "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.int, "TMPL_INT_2"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.eq),
    ]

    expected = [
        pt.TealOp(None, pt.Op.intcblock, "TMPL_INT_1", 0),
        pt.TealOp(None, pt.Op.bytecblock, "TMPL_BYTES_1", "0x00"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.bytec_0, "//", "TMPL_BYTES_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.pushbytes, "TMPL_BYTES_2", "//", "TMPL_BYTES_2"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.bytec_1, "//", "0x00"),
        pt.TealOp(None, pt.Op.bytec_1, "//", "0x00"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.pushbytes, "0x01", "//", "0x01"),
        pt.TealOp(None, pt.Op.concat),
        pt.TealOp(None, pt.Op.len),
        pt.TealOp(None, pt.Op.intc_0, "//", "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.intc_0, "//", "TMPL_INT_1"),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.pushint, "TMPL_INT_2", "//", "TMPL_INT_2"),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.intc_1, "//", 0),
        pt.TealOp(None, pt.Op.intc_1, "//", 0),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.pushint, 1, "//", 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.eq),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_intc():
    """Test scenario where there are more than 4 constants in the intcblock.
    pt.If the 4th constant can't fit in one varuint byte (more than 2**7) it
    should be referenced with the pt.Op.intc 4 command.
    """

    ops = [
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.int, 2**7),
        pt.TealOp(None, pt.Op.int, 2**7),
    ]

    expected = [
        pt.TealOp(None, pt.Op.intcblock, 0, 1, 2, 3, 2**7),
        pt.TealOp(None, pt.Op.intc_0, "//", 0),
        pt.TealOp(None, pt.Op.intc_0, "//", 0),
        pt.TealOp(None, pt.Op.intc_1, "//", 1),
        pt.TealOp(None, pt.Op.intc_1, "//", 1),
        pt.TealOp(None, pt.Op.intc_2, "//", 2),
        pt.TealOp(None, pt.Op.intc_2, "//", 2),
        pt.TealOp(None, pt.Op.intc_3, "//", 3),
        pt.TealOp(None, pt.Op.intc_3, "//", 3),
        pt.TealOp(None, pt.Op.intc, 4, "//", 2**7),
        pt.TealOp(None, pt.Op.intc, 4, "//", 2**7),
    ]

    actual = createConstantBlocks(ops)
    assert actual == expected


def test_createConstantBlocks_small_constant():
    """pt.If a constant cannot be referenced using the intc_[0..3] commands
    and it can be stored in one varuint it byte then pt.Op.pushint is used.
    """

    for cur in range(4, 2**7):
        ops = [
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.int, cur),
            pt.TealOp(None, pt.Op.int, cur),
        ]

        expected = [
            pt.TealOp(None, pt.Op.intcblock, 0, 1, 2, 3),
            pt.TealOp(None, pt.Op.intc_0, "//", 0),
            pt.TealOp(None, pt.Op.intc_0, "//", 0),
            pt.TealOp(None, pt.Op.intc_1, "//", 1),
            pt.TealOp(None, pt.Op.intc_1, "//", 1),
            pt.TealOp(None, pt.Op.intc_2, "//", 2),
            pt.TealOp(None, pt.Op.intc_2, "//", 2),
            pt.TealOp(None, pt.Op.intc_3, "//", 3),
            pt.TealOp(None, pt.Op.intc_3, "//", 3),
            pt.TealOp(None, pt.Op.pushint, cur, "//", cur),
            pt.TealOp(None, pt.Op.pushint, cur, "//", cur),
        ]

        actual = createConstantBlocks(ops)
        assert actual == expected
