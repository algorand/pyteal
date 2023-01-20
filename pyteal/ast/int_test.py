import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_int():
    values = [0, 1, 8, 232323, 2**64 - 1]

    for value in values:
        expr = pt.Int(value)
        assert expr.type_of() == pt.TealType.uint64

        expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.int, value)])

        actual, _ = expr.__teal__(options)

        assert actual == expected


def test_int_invalid():
    with pytest.raises(pt.TealInputError):
        pt.Int(6.7)

    with pytest.raises(pt.TealInputError):
        pt.Int(-1)

    with pytest.raises(pt.TealInputError):
        pt.Int(2**64)

    with pytest.raises(pt.TealInputError):
        pt.Int("0")


def test_enum_int():
    expr = pt.EnumInt("OptIn")
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.int, "OptIn")])

    actual, _ = expr.__teal__(options)

    assert actual == expected
