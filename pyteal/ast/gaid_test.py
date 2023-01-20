import pytest

import pyteal as pt

avm3Options = pt.CompileOptions(version=3)
avm4Options = pt.CompileOptions(version=4)


def test_gaid_teal_3():
    with pytest.raises(pt.TealInputError):
        pt.GeneratedID(0).__teal__(avm3Options)


def test_gaid():
    expr = pt.GeneratedID(0)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.gaid, 0)])

    actual, _ = expr.__teal__(avm4Options)

    assert actual == expected


def test_gaid_invalid():
    with pytest.raises(pt.TealInputError):
        pt.GeneratedID(-1)

    with pytest.raises(pt.TealInputError):
        pt.GeneratedID(pt.MAX_GROUP_SIZE)


def test_gaid_dynamic_teal_3():
    with pytest.raises(pt.TealInputError):
        pt.GeneratedID(pt.Int(0)).__teal__(avm3Options)


def test_gaid_dynamic():
    arg = pt.Int(0)
    expr = pt.GeneratedID(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 0), pt.TealOp(expr, pt.Op.gaids)]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gaid_dynamic_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.GeneratedID(pt.Bytes("index"))
