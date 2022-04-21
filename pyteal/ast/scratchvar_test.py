import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_scratchvar_type():
    myvar_default = pt.ScratchVar()
    assert myvar_default.storage_type() == pt.TealType.anytype
    assert myvar_default.store(pt.Bytes("value")).type_of() == pt.TealType.none
    assert myvar_default.load().type_of() == pt.TealType.anytype

    with pytest.raises(pt.TealTypeError):
        myvar_default.store(pt.Pop(pt.Int(1)))

    myvar_int = pt.ScratchVar(pt.TealType.uint64)
    assert myvar_int.storage_type() == pt.TealType.uint64
    assert myvar_int.store(pt.Int(1)).type_of() == pt.TealType.none
    assert myvar_int.load().type_of() == pt.TealType.uint64

    with pytest.raises(pt.TealTypeError):
        myvar_int.store(pt.Bytes("value"))

    with pytest.raises(pt.TealTypeError):
        myvar_int.store(pt.Pop(pt.Int(1)))

    myvar_bytes = pt.ScratchVar(pt.TealType.bytes)
    assert myvar_bytes.storage_type() == pt.TealType.bytes
    assert myvar_bytes.store(pt.Bytes("value")).type_of() == pt.TealType.none
    assert myvar_bytes.load().type_of() == pt.TealType.bytes

    with pytest.raises(pt.TealTypeError):
        myvar_bytes.store(pt.Int(0))

    with pytest.raises(pt.TealTypeError):
        myvar_bytes.store(pt.Pop(pt.Int(1)))


def test_scratchvar_store():
    myvar = pt.ScratchVar(pt.TealType.bytes)
    arg = pt.Bytes("value")
    expr = myvar.store(arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.byte, '"value"'),
            pt.TealOp(expr, pt.Op.store, myvar.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_scratchvar_load():
    myvar = pt.ScratchVar()
    expr = myvar.load()

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.load, myvar.slot)])

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_scratchvar_index():
    myvar = pt.ScratchVar()
    expr = myvar.index()

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.int, myvar.slot)])

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_scratchvar_assign_store():
    slotId = 2
    myvar = pt.ScratchVar(pt.TealType.uint64, slotId)
    arg = pt.Int(10)
    expr = myvar.store(arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 10),
            pt.TealOp(expr, pt.Op.store, myvar.slot),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_scratchvar_assign_load():
    slotId = 5
    myvar = pt.ScratchVar(slotId=slotId)
    expr = myvar.load()

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.load, myvar.slot)])

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_dynamic_scratchvar_type():
    myvar_default = pt.DynamicScratchVar()
    assert myvar_default.storage_type() == pt.TealType.anytype
    assert myvar_default.store(pt.Bytes("value")).type_of() == pt.TealType.none
    assert myvar_default.load().type_of() == pt.TealType.anytype

    with pytest.raises(pt.TealTypeError):
        myvar_default.store(pt.Pop(pt.Int(1)))

    myvar_int = pt.DynamicScratchVar(pt.TealType.uint64)
    assert myvar_int.storage_type() == pt.TealType.uint64
    assert myvar_int.store(pt.Int(1)).type_of() == pt.TealType.none
    assert myvar_int.load().type_of() == pt.TealType.uint64

    with pytest.raises(pt.TealTypeError):
        myvar_int.store(pt.Bytes("value"))

    with pytest.raises(pt.TealTypeError):
        myvar_int.store(pt.Pop(pt.Int(1)))

    myvar_bytes = pt.DynamicScratchVar(pt.TealType.bytes)
    assert myvar_bytes.storage_type() == pt.TealType.bytes
    assert myvar_bytes.store(pt.Bytes("value")).type_of() == pt.TealType.none
    assert myvar_bytes.load().type_of() == pt.TealType.bytes

    with pytest.raises(pt.TealTypeError):
        myvar_bytes.store(pt.Int(0))

    with pytest.raises(pt.TealTypeError):
        myvar_bytes.store(pt.Pop(pt.Int(1)))


def test_dynamic_scratchvar_load():
    myvar = pt.DynamicScratchVar()
    expr = myvar.load()

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(pt.ScratchLoad(myvar.slot), pt.Op.load, myvar.slot),
            pt.TealOp(expr, pt.Op.loads),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_dynamic_scratchvar_store():
    myvar = pt.DynamicScratchVar(pt.TealType.bytes)
    arg = pt.Bytes("value")
    expr = myvar.store(arg)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(pt.ScratchLoad(myvar.slot), pt.Op.load, myvar.slot),
            pt.TealOp(arg, pt.Op.byte, '"value"'),
            pt.TealOp(expr, pt.Op.stores),
        ]
    )

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_dynamic_scratchvar_index():
    myvar = pt.DynamicScratchVar()
    expr = myvar.index()

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.load, myvar.slot)])

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected


def test_dynamic_scratchvar_cannot_set_index_to_another_dynamic():
    myvar = pt.DynamicScratchVar()
    myvar.load()

    regvar = pt.ScratchVar()
    myvar.set_index(regvar)

    dynvar = pt.DynamicScratchVar()

    with pytest.raises(pt.TealInputError):
        myvar.set_index(dynvar)
