import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_scratch_slot():
    slot = ScratchSlot()
    assert slot == slot
    assert slot.__hash__() == slot.__hash__()
    assert slot != ScratchSlot()

    with TealComponent.Context.ignoreExprEquality():
        assert (
            slot.store().__teal__(options)[0]
            == ScratchStackStore(slot).__teal__(options)[0]
        )
        assert (
            slot.store(Int(1)).__teal__(options)[0]
            == ScratchStore(slot, Int(1)).__teal__(options)[0]
        )

        assert slot.load().type_of() == TealType.anytype
        assert slot.load(TealType.uint64).type_of() == TealType.uint64
        assert (
            slot.load().__teal__(options)[0] == ScratchLoad(slot).__teal__(options)[0]
        )


def test_scratch_load_default():
    slot = ScratchSlot()
    expr = ScratchLoad(slot)
    assert expr.type_of() == TealType.anytype

    expected = TealSimpleBlock([TealOp(expr, Op.load, slot)])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_scratch_load_type():
    for type in (TealType.uint64, TealType.bytes, TealType.anytype):
        slot = ScratchSlot()
        expr = ScratchLoad(slot, type)
        assert expr.type_of() == type

        expected = TealSimpleBlock([TealOp(expr, Op.load, slot)])

        actual, _ = expr.__teal__(options)

        assert actual == expected


def test_scratch_store():
    for value in (
        Int(1),
        Bytes("test"),
        App.globalGet(Bytes("key")),
        If(Int(1), Int(2), Int(3)),
    ):
        slot = ScratchSlot()
        expr = ScratchStore(slot, value)
        assert expr.type_of() == TealType.none

        expected, valueEnd = value.__teal__(options)
        storeBlock = TealSimpleBlock([TealOp(expr, Op.store, slot)])
        valueEnd.setNextBlock(storeBlock)

        actual, _ = expr.__teal__(options)

        assert actual == expected


def test_scratch_stack_store():
    slot = ScratchSlot()
    expr = ScratchStackStore(slot)
    assert expr.type_of() == TealType.none

    expected = TealSimpleBlock([TealOp(expr, Op.store, slot)])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_scratch_assign_id():
    slot = ScratchSlot(255)
    expr = ScratchStackStore(slot)
    assert expr.type_of() == TealType.none

    expected = TealSimpleBlock([TealOp(expr, Op.store, slot)])

    actual, _ = expr.__teal__(options)

    assert actual == expected


def test_scratch_assign_id_invalid():
    with pytest.raises(TealInputError):
        slot = ScratchSlot(-1)

    with pytest.raises(TealInputError):
        slot = ScratchSlot(NUM_SLOTS)
