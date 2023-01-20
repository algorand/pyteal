import pytest

import pyteal as pt

from pyteal.compiler.scratchslots import (
    collectScratchSlots,
    assignScratchSlotsToSubroutines,
)


def test_collectScratchSlots():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.bytes)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

    globalSlot1 = pt.ScratchSlot()

    subroutine1Slot1 = pt.ScratchSlot()
    subroutine1Slot2 = pt.ScratchSlot()
    subroutine1Ops = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, subroutine1Slot1),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.store, subroutine1Slot2),
        pt.TealOp(None, pt.Op.load, globalSlot1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine2Slot1 = pt.ScratchSlot()
    subroutine2Ops = [
        pt.TealOp(None, pt.Op.byte, '"value"'),
        pt.TealOp(None, pt.Op.store, subroutine2Slot1),
        pt.TealOp(None, pt.Op.load, subroutine2Slot1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine3Ops = [
        pt.TealOp(None, pt.Op.retsub),
    ]

    mainSlot1 = pt.ScratchSlot()
    mainSlot2 = pt.ScratchSlot()
    mainOps = [
        pt.TealOp(None, pt.Op.int, 7),
        pt.TealOp(None, pt.Op.store, globalSlot1),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, mainSlot1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.store, mainSlot2),
        pt.TealOp(None, pt.Op.load, mainSlot1),
        pt.TealOp(None, pt.Op.return_),
    ]

    subroutineBlocks = {
        None: pt.TealSimpleBlock(mainOps),
        subroutine1: pt.TealSimpleBlock(subroutine1Ops),
        subroutine2: pt.TealSimpleBlock(subroutine2Ops),
        subroutine3: pt.TealSimpleBlock(subroutine3Ops),
    }

    expected_global = {globalSlot1}

    expected_local = {
        None: {mainSlot1, mainSlot2},
        subroutine1: {subroutine1Slot1, subroutine1Slot2},
        subroutine2: {subroutine2Slot1},
        subroutine3: set(),
    }

    actual_global, actual_local = collectScratchSlots(subroutineBlocks)

    assert actual_global == expected_global
    assert actual_local == expected_local


def test_assignScratchSlotsToSubroutines_no_requested_ids():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.bytes)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

    globalSlot1 = pt.ScratchSlot()

    subroutine1Slot1 = pt.ScratchSlot()
    subroutine1Slot2 = pt.ScratchSlot()
    subroutine1Ops = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, subroutine1Slot1),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.store, subroutine1Slot2),
        pt.TealOp(None, pt.Op.load, globalSlot1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine2Slot1 = pt.ScratchSlot()
    subroutine2Ops = [
        pt.TealOp(None, pt.Op.byte, '"value"'),
        pt.TealOp(None, pt.Op.store, subroutine2Slot1),
        pt.TealOp(None, pt.Op.load, subroutine2Slot1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine3Ops = [
        pt.TealOp(None, pt.Op.retsub),
    ]

    mainSlot1 = pt.ScratchSlot()
    mainSlot2 = pt.ScratchSlot()
    mainOps = [
        pt.TealOp(None, pt.Op.int, 7),
        pt.TealOp(None, pt.Op.store, globalSlot1),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, mainSlot1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.store, mainSlot2),
        pt.TealOp(None, pt.Op.load, mainSlot1),
        pt.TealOp(None, pt.Op.return_),
    ]

    subroutineBlocks = {
        None: pt.TealSimpleBlock(mainOps),
        subroutine1: pt.TealSimpleBlock(subroutine1Ops),
        subroutine2: pt.TealSimpleBlock(subroutine2Ops),
        subroutine3: pt.TealSimpleBlock(subroutine3Ops),
    }

    expectedAssignments = {
        globalSlot1: 0,
        subroutine1Slot1: 1,
        subroutine1Slot2: 2,
        subroutine2Slot1: 3,
        mainSlot1: 4,
        mainSlot2: 5,
    }

    expected = {
        None: {expectedAssignments[mainSlot1], expectedAssignments[mainSlot2]},
        subroutine1: {
            expectedAssignments[subroutine1Slot1],
            expectedAssignments[subroutine1Slot2],
        },
        subroutine2: {expectedAssignments[subroutine2Slot1]},
        subroutine3: set(),
    }

    actual = assignScratchSlotsToSubroutines(subroutineBlocks)

    assert actual == expected

    assert subroutine1Ops == [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, expectedAssignments[subroutine1Slot1]),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.store, expectedAssignments[subroutine1Slot2]),
        pt.TealOp(None, pt.Op.load, expectedAssignments[globalSlot1]),
        pt.TealOp(None, pt.Op.retsub),
    ]

    assert subroutine2Ops == [
        pt.TealOp(None, pt.Op.byte, '"value"'),
        pt.TealOp(None, pt.Op.store, expectedAssignments[subroutine2Slot1]),
        pt.TealOp(None, pt.Op.load, expectedAssignments[subroutine2Slot1]),
        pt.TealOp(None, pt.Op.retsub),
    ]

    assert subroutine3Ops == [
        pt.TealOp(None, pt.Op.retsub),
    ]

    assert mainOps == [
        pt.TealOp(None, pt.Op.int, 7),
        pt.TealOp(None, pt.Op.store, expectedAssignments[globalSlot1]),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, expectedAssignments[mainSlot1]),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.store, expectedAssignments[mainSlot2]),
        pt.TealOp(None, pt.Op.load, expectedAssignments[mainSlot1]),
        pt.TealOp(None, pt.Op.return_),
    ]


def test_assignScratchSlotsToSubroutines_with_requested_ids():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.bytes)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

    globalSlot1 = pt.ScratchSlot(requestedSlotId=8)

    subroutine1Slot1 = pt.ScratchSlot()
    subroutine1Slot2 = pt.ScratchSlot(requestedSlotId=5)
    subroutine1Ops = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, subroutine1Slot1),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.store, subroutine1Slot2),
        pt.TealOp(None, pt.Op.load, globalSlot1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine2Slot1 = pt.ScratchSlot()
    subroutine2Ops = [
        pt.TealOp(None, pt.Op.byte, '"value"'),
        pt.TealOp(None, pt.Op.store, subroutine2Slot1),
        pt.TealOp(None, pt.Op.load, subroutine2Slot1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine3Ops = [
        pt.TealOp(None, pt.Op.retsub),
    ]

    mainSlot1 = pt.ScratchSlot()
    mainSlot2 = pt.ScratchSlot(requestedSlotId=100)
    mainOps = [
        pt.TealOp(None, pt.Op.int, 7),
        pt.TealOp(None, pt.Op.store, globalSlot1),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, mainSlot1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.store, mainSlot2),
        pt.TealOp(None, pt.Op.load, mainSlot1),
        pt.TealOp(None, pt.Op.return_),
    ]

    subroutineBlocks = {
        None: pt.TealSimpleBlock(mainOps),
        subroutine1: pt.TealSimpleBlock(subroutine1Ops),
        subroutine2: pt.TealSimpleBlock(subroutine2Ops),
        subroutine3: pt.TealSimpleBlock(subroutine3Ops),
    }

    expectedAssignments = {
        globalSlot1: 8,
        subroutine1Slot1: 0,
        subroutine1Slot2: 5,
        subroutine2Slot1: 1,
        mainSlot1: 2,
        mainSlot2: 100,
    }

    expected = {
        None: {expectedAssignments[mainSlot1], expectedAssignments[mainSlot2]},
        subroutine1: {
            expectedAssignments[subroutine1Slot1],
            expectedAssignments[subroutine1Slot2],
        },
        subroutine2: {expectedAssignments[subroutine2Slot1]},
        subroutine3: set(),
    }

    actual = assignScratchSlotsToSubroutines(subroutineBlocks)

    assert actual == expected

    assert subroutine1Ops == [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, expectedAssignments[subroutine1Slot1]),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.store, expectedAssignments[subroutine1Slot2]),
        pt.TealOp(None, pt.Op.load, expectedAssignments[globalSlot1]),
        pt.TealOp(None, pt.Op.retsub),
    ]

    assert subroutine2Ops == [
        pt.TealOp(None, pt.Op.byte, '"value"'),
        pt.TealOp(None, pt.Op.store, expectedAssignments[subroutine2Slot1]),
        pt.TealOp(None, pt.Op.load, expectedAssignments[subroutine2Slot1]),
        pt.TealOp(None, pt.Op.retsub),
    ]

    assert subroutine3Ops == [
        pt.TealOp(None, pt.Op.retsub),
    ]

    assert mainOps == [
        pt.TealOp(None, pt.Op.int, 7),
        pt.TealOp(None, pt.Op.store, expectedAssignments[globalSlot1]),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, expectedAssignments[mainSlot1]),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.store, expectedAssignments[mainSlot2]),
        pt.TealOp(None, pt.Op.load, expectedAssignments[mainSlot1]),
        pt.TealOp(None, pt.Op.return_),
    ]


def test_assignScratchSlotsToSubroutines_invalid_requested_id():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.bytes)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

    globalSlot1 = pt.ScratchSlot(requestedSlotId=8)

    subroutine1Slot1 = pt.ScratchSlot()
    subroutine1Slot2 = pt.ScratchSlot(requestedSlotId=5)
    subroutine1Ops = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, subroutine1Slot1),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.store, subroutine1Slot2),
        pt.TealOp(None, pt.Op.load, globalSlot1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine2Slot1 = pt.ScratchSlot(requestedSlotId=100)
    subroutine2Ops = [
        pt.TealOp(None, pt.Op.byte, '"value"'),
        pt.TealOp(None, pt.Op.store, subroutine2Slot1),
        pt.TealOp(None, pt.Op.load, subroutine2Slot1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine3Ops = [
        pt.TealOp(None, pt.Op.retsub),
    ]

    mainSlot1 = pt.ScratchSlot()
    mainSlot2 = pt.ScratchSlot(requestedSlotId=100)
    mainOps = [
        pt.TealOp(None, pt.Op.int, 7),
        pt.TealOp(None, pt.Op.store, globalSlot1),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, mainSlot1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.store, mainSlot2),
        pt.TealOp(None, pt.Op.load, mainSlot1),
        pt.TealOp(None, pt.Op.return_),
    ]

    subroutineBlocks = {
        None: pt.TealSimpleBlock(mainOps),
        subroutine1: pt.TealSimpleBlock(subroutine1Ops),
        subroutine2: pt.TealSimpleBlock(subroutine2Ops),
        subroutine3: pt.TealSimpleBlock(subroutine3Ops),
    }

    # mainSlot2 and subroutine2Slot1 request the same ID, 100
    with pytest.raises(pt.TealInternalError):
        assignScratchSlotsToSubroutines(subroutineBlocks)


def test_assignScratchSlotsToSubroutines_slot_used_before_assignment():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.bytes)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

    globalSlot1 = pt.ScratchSlot()

    subroutine1Slot1 = pt.ScratchSlot()
    subroutine1Slot2 = pt.ScratchSlot()
    subroutine1Ops = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, subroutine1Slot1),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.store, subroutine1Slot2),
        pt.TealOp(None, pt.Op.load, globalSlot1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine2Slot1 = pt.ScratchSlot()
    subroutine2Ops = [
        pt.TealOp(None, pt.Op.byte, '"value"'),
        pt.TealOp(None, pt.Op.store, subroutine2Slot1),
        pt.TealOp(None, pt.Op.load, subroutine2Slot1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine3Ops = [
        pt.TealOp(None, pt.Op.retsub),
    ]

    mainSlot1 = pt.ScratchSlot()
    mainSlot2 = pt.ScratchSlot()
    mainOps = [
        pt.TealOp(None, pt.Op.int, 7),
        pt.TealOp(None, pt.Op.store, globalSlot1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.store, mainSlot2),
        pt.TealOp(None, pt.Op.load, mainSlot1),
        pt.TealOp(None, pt.Op.return_),
    ]

    subroutineBlocks = {
        None: pt.TealSimpleBlock(mainOps),
        subroutine1: pt.TealSimpleBlock(subroutine1Ops),
        subroutine2: pt.TealSimpleBlock(subroutine2Ops),
        subroutine3: pt.TealSimpleBlock(subroutine3Ops),
    }

    with pytest.raises(pt.TealInternalError):
        assignScratchSlotsToSubroutines(subroutineBlocks)
