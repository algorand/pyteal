import pytest

import pyteal as pt

options = pt.CompileOptions()


def test_scratch_slot():
    slot = pt.ScratchSlot()
    assert slot == slot
    assert slot.__hash__() == slot.__hash__()
    assert slot != pt.ScratchSlot()

    with pt.TealComponent.Context.ignoreExprEquality():
        assert (
            slot.store().__teal__(options)[0]
            == pt.ScratchStackStore(slot).__teal__(options)[0]
        )
        assert (
            slot.store(pt.Int(1)).__teal__(options)[0]
            == pt.ScratchStore(slot, pt.Int(1)).__teal__(options)[0]
        )

        assert slot.load().type_of() == pt.TealType.anytype
        assert slot.load(pt.TealType.uint64).type_of() == pt.TealType.uint64
        assert (
            slot.load().__teal__(options)[0]
            == pt.ScratchLoad(slot).__teal__(options)[0]
        )


def test_scratch_load_default():
    slot = pt.ScratchSlot()
    expr = pt.ScratchLoad(slot)
    assert expr.type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.load, slot)])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_scratch_load_index_expression():
    expr = pt.ScratchLoad(slot=None, index_expression=pt.Int(1337))
    assert expr.type_of() == pt.TealType.anytype

    expected = pt.TealSimpleBlock([pt.TealOp(pt.Int(1337), pt.Op.int, 1337)])
    expected.setNextBlock(pt.TealSimpleBlock([pt.TealOp(None, pt.Op.loads)]))

    actual, _ = expr.__teal__(options)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_scratch_load_type():
    for type in (pt.TealType.uint64, pt.TealType.bytes, pt.TealType.anytype):
        slot = pt.ScratchSlot()
        expr = pt.ScratchLoad(slot, type)
        assert expr.type_of() == type

        expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.load, slot)])

        actual, _ = expr.__teal__(options)

        assert actual == expected


def test_scratch_store():
    for value in (
        pt.Int(1),
        pt.Bytes("test"),
        pt.App.globalGet(pt.Bytes("key")),
        pt.If(pt.Int(1), pt.Int(2), pt.Int(3)),
    ):
        slot = pt.ScratchSlot()
        expr = pt.ScratchStore(slot, value)
        assert expr.type_of() == pt.TealType.none

        expected, valueEnd = value.__teal__(options)
        storeBlock = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.store, slot)])
        valueEnd.setNextBlock(storeBlock)

        actual, _ = expr.__teal__(options)

        assert actual == expected


def test_scratch_store_index_expression():
    for value in (
        pt.Int(1),
        pt.Bytes("test"),
        pt.App.globalGet(pt.Bytes("key")),
        pt.If(pt.Int(1), pt.Int(2), pt.Int(3)),
    ):
        expr = pt.ScratchStore(slot=None, value=value, index_expression=pt.Int(1337))
        assert expr.type_of() == pt.TealType.none

        expected = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 1337)])
        valueStart, valueEnd = value.__teal__(options)
        expected.setNextBlock(valueStart)

        storeBlock = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.stores)])
        valueEnd.setNextBlock(storeBlock)

        actual, _ = expr.__teal__(options)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected


def test_scratch_stack_store():
    slot = pt.ScratchSlot()
    expr = pt.ScratchStackStore(slot)
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.store, slot)])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_scratch_assign_id():
    slot = pt.ScratchSlot(255)
    expr = pt.ScratchStackStore(slot)
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.store, slot)])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_scratch_assign_id_invalid():
    with pytest.raises(pt.TealInputError):
        pt.ScratchSlot(-1)

    with pytest.raises(pt.TealInputError):
        pt.ScratchSlot(pt.NUM_SLOTS)


def test_scratch_index():
    slot = pt.ScratchSlot()

    index = pt.ScratchIndex(slot)
    assert index.slot is slot

    assert str(index) == "(ScratchIndex " + str(slot) + ")"

    assert index.type_of() == pt.TealType.uint64

    assert not index.has_return()

    expected = pt.TealSimpleBlock([pt.TealOp(index, pt.Op.int, slot)])
    actual, _ = index.__teal__(options)

    assert actual == expected
