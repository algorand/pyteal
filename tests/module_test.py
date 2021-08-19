from pyteal import *


def test_export_int():
    from pyteal import ast

    assert int != ast.int
