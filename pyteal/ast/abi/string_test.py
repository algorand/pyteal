from .type_test import ContainerType
from os import urandom

from ... import *

import pytest

options = CompileOptions(version=5)


def test_String_encode():
    value = abi.String()

    tspec = value.type_spec() 
    assert tspec.is_dynamic()
    assert str(tspec) == "string"

    expr = value.encode()
    assert expr.type_of() == TealType.bytes
    assert not expr.has_return()
    

    expected = TealSimpleBlock([TealOp(expr, Op.load, value.stored_value.slot)])
    actual, _ = expr.__teal__(options)
    assert actual == expected
    assert expr == value.get()


def test_String_decode():
    pass

def test_String_get():
    pass
