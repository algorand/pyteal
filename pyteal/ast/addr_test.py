import pytest

from .. import *


def test_addr():
    expr = Addr("NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3THMF")
    assert expr.type_of() == TealType.bytes
    expected = TealSimpleBlock(
        [
            TealOp(
                expr,
                Op.addr,
                "NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3THMF",
            )
        ]
    )
    actual, _ = expr.__teal__(CompileOptions())
    assert actual == expected


def test_addr_invalid():
    with pytest.raises(TealInputError):
        Addr("NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3TH")

    with pytest.raises(TealInputError):
        Addr("000000000000000000000000000000000000000000000000000000000")

    with pytest.raises(TealInputError):
        Addr(2)
