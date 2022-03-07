import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_scratchvar_type():
    myvar_default = ScratchVar()
    assert myvar_default.storage_type() == TealType.anytype
    assert myvar_default.store(Bytes("value")).type_of() == TealType.none
    assert myvar_default.load().type_of() == TealType.anytype

    with pytest.raises(TealTypeError):
        myvar_default.store(Pop(Int(1)))

    myvar_int = ScratchVar(TealType.uint64)
    assert myvar_int.storage_type() == TealType.uint64
    assert myvar_int.store(Int(1)).type_of() == TealType.none
    assert myvar_int.load().type_of() == TealType.uint64

    with pytest.raises(TealTypeError):
        myvar_int.store(Bytes("value"))

    with pytest.raises(TealTypeError):
        myvar_int.store(Pop(Int(1)))

    myvar_bytes = ScratchVar(TealType.bytes)
    assert myvar_bytes.storage_type() == TealType.bytes
    assert myvar_bytes.store(Bytes("value")).type_of() == TealType.none
    assert myvar_bytes.load().type_of() == TealType.bytes

    with pytest.raises(TealTypeError):
        myvar_bytes.store(Int(0))

    with pytest.raises(TealTypeError):
        myvar_bytes.store(Pop(Int(1)))


def test_scratchvar_store():
    myvar = ScratchVar(TealType.bytes)
    arg = Bytes("value")
    expr = myvar.store(arg)

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.byte, '"value"'),
            TealOp(expr, Op.store, myvar.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_scratchvar_load():
    myvar = ScratchVar()
    expr = myvar.load()

    expected = TealSimpleBlock([TealOp(expr, Op.load, myvar.slot)])

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_scratchvar_assign_store():
    slotId = 2
    myvar = ScratchVar(TealType.uint64, slotId)
    arg = Int(10)
    expr = myvar.store(arg)

    expected = TealSimpleBlock(
        [
            TealOp(arg, Op.int, 10),
            TealOp(expr, Op.store, myvar.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_scratchvar_assign_load():
    slotId = 5
    myvar = ScratchVar(slotId=slotId)
    expr = myvar.load()

    expected = TealSimpleBlock([TealOp(expr, Op.load, myvar.slot)])

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected
