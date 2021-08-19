import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import MAX_GROUP_SIZE, NUM_SLOTS, CompileOptions

teal3Options = CompileOptions(version=3)
teal4Options = CompileOptions(version=4)


def test_gload_teal_3():
    with pytest.raises(TealInputError):
        ImportScratchValue(0, 1).__teal__(teal3Options)

    with pytest.raises(TealInputError):
        ImportScratchValue(Int(0), 1).__teal__(teal3Options)


def test_gload():
    expr = ImportScratchValue(0, 1)
    assert expr.type_of() == TealType.anytype

    expected = TealSimpleBlock([TealOp(expr, Op.gload, 0, 1)])

    actual, _ = expr.__teal__(teal4Options)

    assert actual == expected


def test_gload_dynamic():
    arg = Int(1)
    expr = ImportScratchValue(arg, 0)
    assert expr.type_of() == TealType.anytype

    expected = TealSimpleBlock([TealOp(arg, Op.int, 1), TealOp(expr, Op.gloads, 0)])

    actual, _ = expr.__teal__(teal4Options)
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
