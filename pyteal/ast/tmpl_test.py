import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_tmpl_int():
    expr = pt.Tmpl.Int("TMPL_AMNT")
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.int, "TMPL_AMNT")])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_tmpl_int_invalid():
    with pytest.raises(pt.TealInputError):
        pt.Tmpl.Int("whatever")


def test_tmpl_bytes():
    expr = pt.Tmpl.Bytes("TMPL_NOTE")
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.byte, "TMPL_NOTE")])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_tmpl_bytes_invalid():
    with pytest.raises(pt.TealInputError):
        pt.Tmpl.Bytes("whatever")


def test_tmpl_addr():
    expr = pt.Tmpl.Addr("TMPL_RECEIVER0")
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.addr, "TMPL_RECEIVER0")])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_tmpl_addr_invalid():
    with pytest.raises(pt.TealInputError):
        pt.Tmpl.Addr("whatever")
