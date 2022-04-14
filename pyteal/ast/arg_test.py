import pytest

import pyteal as pt

teal2Options = pt.CompileOptions(version=2)
teal4Options = pt.CompileOptions(version=4)
teal5Options = pt.CompileOptions(version=5)


def test_arg_static():
    for i in range(256):
        expr = pt.Arg(i)
        assert expr.type_of() == pt.TealType.bytes
        assert not expr.has_return()

        expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.arg, i)])

        actual, _ = expr.__teal__(teal2Options)
        assert actual == expected


def test_arg_dynamic():
    i = pt.Int(7)
    expr = pt.Arg(i)
    assert expr.type_of() == pt.TealType.bytes
    assert not expr.has_return()

    expected = pt.TealSimpleBlock(
        [pt.TealOp(i, pt.Op.int, 7), pt.TealOp(expr, pt.Op.args)]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(teal4Options)


def test_arg_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Arg(pt.Bytes("k"))

    with pytest.raises(pt.TealInputError):
        pt.Arg(-1)

    with pytest.raises(pt.TealInputError):
        pt.Arg(256)
