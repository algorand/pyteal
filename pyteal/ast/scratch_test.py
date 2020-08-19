import pytest

from .. import *

def test_scratch_slot():
    slot = ScratchSlot()
    assert slot == slot
    assert slot.__hash__() == slot.__hash__()
    assert slot != ScratchSlot()

    assert slot.store().__teal__() == ScratchStore(slot).__teal__()

    assert slot.load().type_of() == TealType.anytype
    assert slot.load(TealType.uint64).type_of() == TealType.uint64
    assert slot.load().__teal__() == ScratchLoad(slot).__teal__()

def test_scratch_load_default():
    slot = ScratchSlot()
    expr = ScratchLoad(slot)
    assert expr.type_of() == TealType.anytype
    assert expr.__teal__() == [
        TealOp(Op.load, slot)
    ]

def test_scratch_load_type():
    for type in (TealType.uint64, TealType.bytes, TealType.anytype):
        slot = ScratchSlot()
        expr = ScratchLoad(slot, type)
        assert expr.type_of() == type
        assert expr.__teal__() == [
            TealOp(Op.load, slot)
        ]

def test_scratch_store():
    slot = ScratchSlot()
    expr = ScratchStore(slot)
    assert expr.type_of() == TealType.none
    assert expr.__teal__() == [
        TealOp(Op.store, slot)
    ]
