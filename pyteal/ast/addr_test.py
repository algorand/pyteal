import pytest

import pyteal as pt


def test_addr():
    expr = pt.Addr("NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3THMF")
    assert expr.type_of() == pt.TealType.bytes
    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(
                expr,
                pt.Op.addr,
                "NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3THMF",
            )
        ]
    )
    actual, _ = expr.__teal__(pt.CompileOptions())
    assert actual == expected


def test_addr_invalid():
    with pytest.raises(pt.TealInputError):
        pt.Addr("NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3TH")

    with pytest.raises(pt.TealInputError):
        pt.Addr("000000000000000000000000000000000000000000000000000000000")

    with pytest.raises(pt.TealInputError):
        pt.Addr(2)
