import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import MAX_GROUP_SIZE, NUM_SLOTS, CompileOptions

teal3Options = CompileOptions(version=3)
teal4Options = CompileOptions(version=4)
teal6Options = CompileOptions(version=6)


def test_gload_teal_3():
    with pytest.raises(TealInputError):
        ImportScratchValue(0, 1).__teal__(teal3Options)

    with pytest.raises(TealInputError):
        ImportScratchValue(Int(0), 1).__teal__(teal3Options)

    with pytest.raises(TealInputError):
        ImportScratchValue(Int(0), Int(1)).__teal__(teal3Options)


def test_gload_teal_4():
    with pytest.raises(TealInputError):
        ImportScratchValue(Int(0), Int(2)).__teal__(teal4Options)


def test_gload():
    expr = ImportScratchValue(0, 1)
    assert expr.type_of() == TealType.anytype

    expected = TealSimpleBlock([TealOp(expr, Op.gload, 0, 1)])

    actual, _ = expr.__teal__(teal4Options)

    assert actual == expected


def test_gloads():
    arg = Int(1)
    expr = ImportScratchValue(arg, 0)
    assert expr.type_of() == TealType.anytype

    expected = TealSimpleBlock([TealOp(arg, Op.int, 1), TealOp(expr, Op.gloads, 0)])

    actual, _ = expr.__teal__(teal4Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gloadss():
    txID = Int(1)
    slotID = Int(0)
    expr = ImportScratchValue(txID, slotID)
    assert expr.type_of() == TealType.anytype

    expected = TealSimpleBlock(
        [TealOp(txID, Op.int, 1), TealOp(slotID, Op.int, 0), TealOp(expr, Op.gloadss)]
    )

    actual, _ = expr.__teal__(teal6Options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_gload_invalid():
    with pytest.raises(TealInputError):
        ImportScratchValue(-1, 0)

    with pytest.raises(TealInputError):
        ImportScratchValue(MAX_GROUP_SIZE, 0)

    with pytest.raises(TealInputError):
        ImportScratchValue(0, -1)

    with pytest.raises(TealInputError):
        ImportScratchValue(0, NUM_SLOTS)

    with pytest.raises(TealInputError):
        ImportScratchValue(0, Int(0))

    with pytest.raises(TealTypeError):
        ImportScratchValue(Bytes("AQID"), 0)  # byte encoding of [1, 2, 3]
