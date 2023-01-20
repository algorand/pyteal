import pytest

import pyteal as pt

avm3Options = pt.CompileOptions(version=3)
avm4Options = pt.CompileOptions(version=4)
avm6Options = pt.CompileOptions(version=6)


def test_gload_teal_3():
    with pytest.raises(pt.TealInputError):
        pt.ImportScratchValue(0, 1).__teal__(avm3Options)

    with pytest.raises(pt.TealInputError):
        pt.ImportScratchValue(pt.Int(0), 1).__teal__(avm3Options)

    with pytest.raises(pt.TealInputError):
        pt.ImportScratchValue(pt.Int(0), pt.Int(1)).__teal__(avm3Options)


def test_gload_teal_4():
    with pytest.raises(pt.TealInputError):
        pt.ImportScratchValue(pt.Int(0), pt.Int(2)).__teal__(avm4Options)


def test_gload():
    expr = pt.ImportScratchValue(0, 1)
    assert expr.type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.gload, 0, 1)])

    actual, _ = expr.__teal__(avm4Options)

    assert actual == expected


def test_gloads():
    arg = pt.Int(1)
    expr = pt.ImportScratchValue(arg, 0)
    assert expr.type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg, pt.Op.int, 1), pt.TealOp(expr, pt.Op.gloads, 0)]
    )

    actual, _ = expr.__teal__(avm4Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gloadss():
    txID = pt.Int(1)
    slotID = pt.Int(0)
    expr = pt.ImportScratchValue(txID, slotID)
    assert expr.type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(txID, pt.Op.int, 1),
            pt.TealOp(slotID, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.gloadss),
        ]
    )

    actual, _ = expr.__teal__(avm6Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gload_invalid():
    with pytest.raises(pt.TealInputError):
        pt.ImportScratchValue(-1, 0)

    with pytest.raises(pt.TealInputError):
        pt.ImportScratchValue(pt.MAX_GROUP_SIZE, 0)

    with pytest.raises(pt.TealInputError):
        pt.ImportScratchValue(0, -1)

    with pytest.raises(pt.TealInputError):
        pt.ImportScratchValue(0, pt.NUM_SLOTS)

    with pytest.raises(pt.TealInputError):
        pt.ImportScratchValue(0, pt.Int(0))

    with pytest.raises(pt.TealTypeError):
        pt.ImportScratchValue(pt.Bytes("AQID"), 0)  # byte encoding of [1, 2, 3]
