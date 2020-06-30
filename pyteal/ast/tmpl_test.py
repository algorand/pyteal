import pytest

from .. import *

def test_tmpl_int():
    expr = Tmpl.Int("TMPL_AMNT")
    assert expr.type_of() == TealType.uint64
    assert expr.__teal__() == [
        TealOp(Op.int, "TMPL_AMNT")
    ]

def test_tmpl_int_invalid():
    with pytest.raises(TealInputError):
        Tmpl.Int("whatever")

def test_tmpl_bytes():
    expr = Tmpl.Bytes("TMPL_NOTE")
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.byte, "TMPL_NOTE")
    ]

def test_tmpl_bytes_invalid():
    with pytest.raises(TealInputError):
        Tmpl.Bytes("whatever")

def test_tmpl_addr():
    expr = Tmpl.Addr("TMPL_RECEIVER0")
    assert expr.type_of() == TealType.bytes
    assert expr.__teal__() == [
        TealOp(Op.addr, "TMPL_RECEIVER0")
    ]

def test_tmpl_addr_invalid():
    with pytest.raises(TealInputError):
        Tmpl.Addr("whatever")
