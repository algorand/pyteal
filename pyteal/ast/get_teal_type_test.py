from .. import *


def test_get_teal_type_str():
    assert get_teal_type("str") == Bytes("str")


def test_get_teal_type_int():
    assert get_teal_type(1) == Int(1)


def test_get_teal_type_pyteal_bytes():
    assert get_teal_type(Bytes("str")) == Bytes("str")


def test_get_teal_type_pyteal_int():
    assert get_teal_type(Int(1)) == Int(1)
