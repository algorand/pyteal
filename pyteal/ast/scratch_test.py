import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_scratch_init():
    ######## ScratchSlot.__init__() #########

    slot = ScratchSlot()
    assert slot.dynamic() is False
    assert slot.id >= 0

    slot_with_requested = ScratchSlot(42)
    assert slot_with_requested.dynamic() is False
    assert slot_with_requested.id == 42

    slot_with_requested = ScratchSlot(requestedSlotId=42)
    assert slot_with_requested.dynamic() is False
    assert slot_with_requested.id == 42

    with pytest.raises(AssertionError) as e:
        ScratchSlot(Int(42))

    assert "requestedSlotId must be an int but was provided " in str(e)

    ######## DynamicSlot.__init__() #########

    with pytest.raises(TypeError):
        dynamic_slot = DynamicSlot()

    dynamic_with_slotExpr = DynamicSlot(Int(42))
    assert dynamic_with_slotExpr.dynamic() is True
    assert dynamic_with_slotExpr.id == Int(42)

    dynamic_with_slotExpr = DynamicSlot(slotIdExpr=Int(1337))
    assert dynamic_with_slotExpr.dynamic() is True
    assert dynamic_with_slotExpr.id == Int(1337)

    with pytest.raises(AssertionError) as e:
        DynamicSlot(42)

    assert "slotIdExpr must be an Expr but was provided " in str(e)


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
