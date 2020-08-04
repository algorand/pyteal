import pytest

from .. import *

def test_tmpl_int():
    expr = Tmpl.Int("TMPL_AMNT")
    assert expr.__teal__() == [
        ["int", "TMPL_AMNT"]
    ]

def test_tmpl_int_invalid():
    with pytest.raises(TealInputError):
        Tmpl.Int("whatever")

def test_tmpl_bytes():
    expr = Tmpl.Bytes("TMPL_NOTE")
    assert expr.__teal__() == [
        ["byte", "TMPL_NOTE"]
    ]

def test_tmpl_bytes_invalid():
    with pytest.raises(TealInputError):
        Tmpl.Bytes("whatever")

def test_tmpl_addr():
    expr = Tmpl.Addr("TMPL_RECEIVER0")
    assert expr.__teal__() == [
        ["addr", "TMPL_RECEIVER0"]
    ]

def test_tmpl_addr_invalid():
    with pytest.raises(TealInputError):
        Tmpl.Addr("whatever")
