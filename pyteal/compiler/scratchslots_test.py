import pytest

from .. import *

from .scratchslots import collectScratchSlots, assignScratchSlotsToSubroutines


def test_collectScratchSlots():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub2Impl, TealType.bytes)
    subroutine3 = SubroutineDefinition(sub3Impl, TealType.none)

    globalSlot1 = ScratchSlot()

    subroutine1Slot1 = ScratchSlot()
    subroutine1Slot2 = ScratchSlot()
    subroutine1Ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, subroutine1Slot1),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.store, subroutine1Slot2),
        TealOp(None, Op.load, globalSlot1),
        TealOp(None, Op.retsub),
    ]

    subroutine2Slot1 = ScratchSlot()
    subroutine2Ops = [
        TealOp(None, Op.byte, '"value"'),
        TealOp(None, Op.store, subroutine2Slot1),
        TealOp(None, Op.load, subroutine2Slot1),
        TealOp(None, Op.retsub),
    ]

    subroutine3Ops = [
        TealOp(None, Op.retsub),
    ]

    mainSlot1 = ScratchSlot()
    mainSlot2 = ScratchSlot()
    mainOps = [
        TealOp(None, Op.int, 7),
        TealOp(None, Op.store, globalSlot1),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, mainSlot1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.store, mainSlot2),
        TealOp(None, Op.load, mainSlot1),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    expected = {
        None: {globalSlot1, mainSlot1, mainSlot2},
        subroutine1: {globalSlot1, subroutine1Slot1, subroutine1Slot2},
        subroutine2: {subroutine2Slot1},
        subroutine3: set(),
    }

    actual = collectScratchSlots(subroutineMapping)

    assert actual == expected


def test_assignScratchSlotsToSubroutines_no_requested_ids():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub2Impl, TealType.bytes)
    subroutine3 = SubroutineDefinition(sub3Impl, TealType.none)

    globalSlot1 = ScratchSlot()

    subroutine1Slot1 = ScratchSlot()
    subroutine1Slot2 = ScratchSlot()
    subroutine1Ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, subroutine1Slot1),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.store, subroutine1Slot2),
        TealOp(None, Op.load, globalSlot1),
        TealOp(None, Op.retsub),
    ]

    subroutine2Slot1 = ScratchSlot()
    subroutine2Ops = [
        TealOp(None, Op.byte, '"value"'),
        TealOp(None, Op.store, subroutine2Slot1),
        TealOp(None, Op.load, subroutine2Slot1),
        TealOp(None, Op.retsub),
    ]

    subroutine3Ops = [
        TealOp(None, Op.retsub),
    ]

    mainSlot1 = ScratchSlot()
    mainSlot2 = ScratchSlot()
    mainOps = [
        TealOp(None, Op.int, 7),
        TealOp(None, Op.store, globalSlot1),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, mainSlot1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.store, mainSlot2),
        TealOp(None, Op.load, mainSlot1),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    subroutineBlocks = {
        None: TealSimpleBlock(mainOps),
        subroutine1: TealSimpleBlock(subroutine1Ops),
        subroutine2: TealSimpleBlock(subroutine2Ops),
        subroutine3: TealSimpleBlock(subroutine3Ops),
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

    actual = assignScratchSlotsToSubroutines(subroutineMapping, subroutineBlocks)

    assert actual == expected

    assert subroutine1Ops == [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, expectedAssignments[subroutine1Slot1]),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.store, expectedAssignments[subroutine1Slot2]),
        TealOp(None, Op.load, expectedAssignments[globalSlot1]),
        TealOp(None, Op.retsub),
    ]

    assert subroutine2Ops == [
        TealOp(None, Op.byte, '"value"'),
        TealOp(None, Op.store, expectedAssignments[subroutine2Slot1]),
        TealOp(None, Op.load, expectedAssignments[subroutine2Slot1]),
        TealOp(None, Op.retsub),
    ]

    assert subroutine3Ops == [
        TealOp(None, Op.retsub),
    ]

    assert mainOps == [
        TealOp(None, Op.int, 7),
        TealOp(None, Op.store, expectedAssignments[globalSlot1]),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, expectedAssignments[mainSlot1]),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.store, expectedAssignments[mainSlot2]),
        TealOp(None, Op.load, expectedAssignments[mainSlot1]),
        TealOp(None, Op.return_),
    ]


def test_assignScratchSlotsToSubroutines_with_requested_ids():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub2Impl, TealType.bytes)
    subroutine3 = SubroutineDefinition(sub3Impl, TealType.none)

    globalSlot1 = ScratchSlot(requestedSlotId=8)

    subroutine1Slot1 = ScratchSlot()
    subroutine1Slot2 = ScratchSlot(requestedSlotId=5)
    subroutine1Ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, subroutine1Slot1),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.store, subroutine1Slot2),
        TealOp(None, Op.load, globalSlot1),
        TealOp(None, Op.retsub),
    ]

    subroutine2Slot1 = ScratchSlot()
    subroutine2Ops = [
        TealOp(None, Op.byte, '"value"'),
        TealOp(None, Op.store, subroutine2Slot1),
        TealOp(None, Op.load, subroutine2Slot1),
        TealOp(None, Op.retsub),
    ]

    subroutine3Ops = [
        TealOp(None, Op.retsub),
    ]

    mainSlot1 = ScratchSlot()
    mainSlot2 = ScratchSlot(requestedSlotId=100)
    mainOps = [
        TealOp(None, Op.int, 7),
        TealOp(None, Op.store, globalSlot1),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, mainSlot1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.store, mainSlot2),
        TealOp(None, Op.load, mainSlot1),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    subroutineBlocks = {
        None: TealSimpleBlock(mainOps),
        subroutine1: TealSimpleBlock(subroutine1Ops),
        subroutine2: TealSimpleBlock(subroutine2Ops),
        subroutine3: TealSimpleBlock(subroutine3Ops),
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

    actual = assignScratchSlotsToSubroutines(subroutineMapping, subroutineBlocks)

    assert actual == expected

    assert subroutine1Ops == [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, expectedAssignments[subroutine1Slot1]),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.store, expectedAssignments[subroutine1Slot2]),
        TealOp(None, Op.load, expectedAssignments[globalSlot1]),
        TealOp(None, Op.retsub),
    ]

    assert subroutine2Ops == [
        TealOp(None, Op.byte, '"value"'),
        TealOp(None, Op.store, expectedAssignments[subroutine2Slot1]),
        TealOp(None, Op.load, expectedAssignments[subroutine2Slot1]),
        TealOp(None, Op.retsub),
    ]

    assert subroutine3Ops == [
        TealOp(None, Op.retsub),
    ]

    assert mainOps == [
        TealOp(None, Op.int, 7),
        TealOp(None, Op.store, expectedAssignments[globalSlot1]),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, expectedAssignments[mainSlot1]),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.store, expectedAssignments[mainSlot2]),
        TealOp(None, Op.load, expectedAssignments[mainSlot1]),
        TealOp(None, Op.return_),
    ]


def test_assignScratchSlotsToSubroutines_invalid_requested_id():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub2Impl, TealType.bytes)
    subroutine3 = SubroutineDefinition(sub3Impl, TealType.none)

    globalSlot1 = ScratchSlot(requestedSlotId=8)

    subroutine1Slot1 = ScratchSlot()
    subroutine1Slot2 = ScratchSlot(requestedSlotId=5)
    subroutine1Ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, subroutine1Slot1),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.store, subroutine1Slot2),
        TealOp(None, Op.load, globalSlot1),
        TealOp(None, Op.retsub),
    ]

    subroutine2Slot1 = ScratchSlot(requestedSlotId=100)
    subroutine2Ops = [
        TealOp(None, Op.byte, '"value"'),
        TealOp(None, Op.store, subroutine2Slot1),
        TealOp(None, Op.load, subroutine2Slot1),
        TealOp(None, Op.retsub),
    ]

    subroutine3Ops = [
        TealOp(None, Op.retsub),
    ]

    mainSlot1 = ScratchSlot()
    mainSlot2 = ScratchSlot(requestedSlotId=100)
    mainOps = [
        TealOp(None, Op.int, 7),
        TealOp(None, Op.store, globalSlot1),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, mainSlot1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.store, mainSlot2),
        TealOp(None, Op.load, mainSlot1),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    subroutineBlocks = {
        None: TealSimpleBlock(mainOps),
        subroutine1: TealSimpleBlock(subroutine1Ops),
        subroutine2: TealSimpleBlock(subroutine2Ops),
        subroutine3: TealSimpleBlock(subroutine3Ops),
    }

    # mainSlot2 and subroutine2Slot1 request the same ID, 100
    with pytest.raises(TealInternalError):
        actual = assignScratchSlotsToSubroutines(subroutineMapping, subroutineBlocks)


def test_assignScratchSlotsToSubroutines_slot_used_before_assignment():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub2Impl, TealType.bytes)
    subroutine3 = SubroutineDefinition(sub3Impl, TealType.none)

    globalSlot1 = ScratchSlot()

    subroutine1Slot1 = ScratchSlot()
    subroutine1Slot2 = ScratchSlot()
    subroutine1Ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, subroutine1Slot1),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.store, subroutine1Slot2),
        TealOp(None, Op.load, globalSlot1),
        TealOp(None, Op.retsub),
    ]

    subroutine2Slot1 = ScratchSlot()
    subroutine2Ops = [
        TealOp(None, Op.byte, '"value"'),
        TealOp(None, Op.store, subroutine2Slot1),
        TealOp(None, Op.load, subroutine2Slot1),
        TealOp(None, Op.retsub),
    ]

    subroutine3Ops = [
        TealOp(None, Op.retsub),
    ]

    mainSlot1 = ScratchSlot()
    mainSlot2 = ScratchSlot()
    mainOps = [
        TealOp(None, Op.int, 7),
        TealOp(None, Op.store, globalSlot1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.store, mainSlot2),
        TealOp(None, Op.load, mainSlot1),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    subroutineBlocks = {
        None: TealSimpleBlock(mainOps),
        subroutine1: TealSimpleBlock(subroutine1Ops),
        subroutine2: TealSimpleBlock(subroutine2Ops),
        subroutine3: TealSimpleBlock(subroutine3Ops),
    }

    with pytest.raises(TealInternalError):
        assignScratchSlotsToSubroutines(subroutineMapping, subroutineBlocks)
