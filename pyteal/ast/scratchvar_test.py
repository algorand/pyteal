from .. import *


def test_scratchvar():
    myvar = ScratchVar()
    assert myvar.store(Bytes("value")).type_of() == TealType.none

    expected = TealSimpleBlock([
        TealOp(Op.byte, "\"value\""),
        TealOp(Op.store, myvar.slot),
    ])

    expr = myvar.store(Bytes("value"))
    actual, _ = expr.__teal__()
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_scratchvar_load():
    myvar = ScratchVar()

    assert myvar.load().type_of() == TealType.anytype

    expected = TealSimpleBlock([
        TealOp(Op.load, myvar.slot),
    ])

    expr = myvar.load()
    actual, _ = expr.__teal__()
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)

    assert actual == expected
