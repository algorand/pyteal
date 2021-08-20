import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_tmpl_int():
    expr = Tmpl.Int("TMPL_AMNT")
    assert expr.type_of() == TealType.uint64

    expected = TealSimpleBlock([TealOp(expr, Op.int, "TMPL_AMNT")])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_tmpl_int_invalid():
    with pytest.raises(TealInputError):
        Tmpl.Int("whatever")


def test_tmpl_bytes():
    expr = Tmpl.Bytes("TMPL_NOTE")
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.byte, "TMPL_NOTE")])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_tmpl_bytes_invalid():
    with pytest.raises(TealInputError):
        Tmpl.Bytes("whatever")


def test_tmpl_addr():
    expr = Tmpl.Addr("TMPL_RECEIVER0")
    assert expr.type_of() == TealType.bytes

    expected = TealSimpleBlock([TealOp(expr, Op.addr, "TMPL_RECEIVER0")])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_tmpl_addr_invalid():
    with pytest.raises(TealInputError):
        Tmpl.Addr("whatever")
