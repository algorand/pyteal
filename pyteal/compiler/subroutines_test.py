from collections import OrderedDict

from .. import *

from .subroutines import (
    findRecursionPoints,
    spillLocalSlotsDuringRecursion,
    resolveSubroutines,
)


def test_findRecursionPoints_empty():
    subroutines = dict()

    expected = dict()
    actual = findRecursionPoints(subroutines)
    assert actual == expected


def test_findRecursionPoints_none():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub2Impl, TealType.bytes)
    subroutine3 = SubroutineDefinition(sub3Impl, TealType.none)

    subroutines = {
        subroutine1: {subroutine2, subroutine3},
        subroutine2: {subroutine3},
        subroutine3: set(),
    }

    expected = {
        subroutine1: set(),
        subroutine2: set(),
        subroutine3: set(),
    }

    actual = findRecursionPoints(subroutines)
    assert actual == expected


def test_findRecursionPoints_direct_recursion():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub2Impl, TealType.bytes)
    subroutine3 = SubroutineDefinition(sub3Impl, TealType.none)

    subroutines = {
        subroutine1: {subroutine2, subroutine3},
        subroutine2: {subroutine2, subroutine3},
        subroutine3: set(),
    }

    expected = {
        subroutine1: set(),
        subroutine2: {subroutine2},
        subroutine3: set(),
    }

    actual = findRecursionPoints(subroutines)
    assert actual == expected


def test_findRecursionPoints_mutual_recursion():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub2Impl, TealType.bytes)
    subroutine3 = SubroutineDefinition(sub3Impl, TealType.none)

    subroutines = {
        subroutine1: {subroutine2, subroutine3},
        subroutine2: {subroutine1, subroutine3},
        subroutine3: set(),
    }

    expected = {
        subroutine1: {subroutine2},
        subroutine2: {subroutine1},
        subroutine3: set(),
    }

    actual = findRecursionPoints(subroutines)
    assert actual == expected


def test_findRecursionPoints_direct_and_mutual_recursion():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub2Impl, TealType.bytes)
    subroutine3 = SubroutineDefinition(sub3Impl, TealType.none)

    subroutines = {
        subroutine1: {subroutine2, subroutine3},
        subroutine2: {subroutine1, subroutine2, subroutine3},
        subroutine3: set(),
    }

    expected = {
        subroutine1: {subroutine2},
        subroutine2: {subroutine1, subroutine2},
        subroutine3: set(),
    }

    actual = findRecursionPoints(subroutines)
    assert actual == expected


def test_spillLocalSlotsDuringRecursion_no_subroutines():
    for version in (4, 5):
        l1Label = LabelReference("l1")
        mainOps = [
            TealOp(None, Op.txn, "Fee"),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bz, l1Label),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.return_),
            TealLabel(None, l1Label),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.return_),
        ]

        subroutineMapping = {None: mainOps}

        subroutineGraph = dict()

        localSlots = {None: set()}

        spillLocalSlotsDuringRecursion(
            version, subroutineMapping, subroutineGraph, localSlots
        )

        assert mainOps == [
            TealOp(None, Op.txn, "Fee"),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bz, l1Label),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.return_),
            TealLabel(None, l1Label),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.return_),
        ]


def test_spillLocalSlotsDuringRecursion_1_subroutine_no_recursion():
    for version in (4, 5):
        subroutine = SubroutineDefinition(lambda: None, TealType.uint64)

        subroutineL1Label = LabelReference("l1")
        subroutineOps = [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bnz, subroutineL1Label),
            TealOp(None, Op.err),
            TealLabel(None, subroutineL1Label),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.retsub),
        ]

        l1Label = LabelReference("l1")
        mainOps = [
            TealOp(None, Op.txn, "Fee"),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bz, l1Label),
            TealOp(None, Op.int, 100),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.return_),
            TealLabel(None, l1Label),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.return_),
        ]

        subroutineMapping = {None: mainOps, subroutine: subroutineOps}

        subroutineGraph = {subroutine: set()}

        localSlots = {None: set(), subroutine: {0}}

        spillLocalSlotsDuringRecursion(
            version, subroutineMapping, subroutineGraph, localSlots
        )

        assert subroutineMapping == {
            None: [
                TealOp(None, Op.txn, "Fee"),
                TealOp(None, Op.int, 0),
                TealOp(None, Op.eq),
                TealOp(None, Op.bz, l1Label),
                TealOp(None, Op.int, 100),
                TealOp(None, Op.callsub, subroutine),
                TealOp(None, Op.return_),
                TealLabel(None, l1Label),
                TealOp(None, Op.int, 0),
                TealOp(None, Op.return_),
            ],
            subroutine: [
                TealOp(None, Op.store, 0),
                TealOp(None, Op.load, 0),
                TealOp(None, Op.int, 0),
                TealOp(None, Op.eq),
                TealOp(None, Op.bnz, subroutineL1Label),
                TealOp(None, Op.err),
                TealLabel(None, subroutineL1Label),
                TealOp(None, Op.int, 1),
                TealOp(None, Op.retsub),
            ],
        }


def test_spillLocalSlotsDuringRecursion_1_subroutine_recursion_v4():
    def sub1Impl(a1):
        return None

    subroutine = SubroutineDefinition(sub1Impl, TealType.uint64)

    subroutineL1Label = LabelReference("l1")
    subroutineOps = [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutineL1Label),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.minus),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutineL1Label),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.retsub),
    ]

    l1Label = LabelReference("l1")
    mainOps = [
        TealOp(None, Op.txn, "Fee"),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bz, l1Label),
        TealOp(None, Op.int, 100),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.return_),
        TealLabel(None, l1Label),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {None: mainOps, subroutine: subroutineOps}

    subroutineGraph = {subroutine: {subroutine}}

    localSlots = {None: set(), subroutine: {0}}

    spillLocalSlotsDuringRecursion(4, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            TealOp(None, Op.txn, "Fee"),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bz, l1Label),
            TealOp(None, Op.int, 100),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.return_),
            TealLabel(None, l1Label),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.return_),
        ],
        subroutine: [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bnz, subroutineL1Label),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.minus),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.dig, 1),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.swap),
            TealOp(None, Op.store, 0),
            TealOp(None, Op.swap),
            TealOp(None, Op.pop),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
            TealOp(None, Op.retsub),
            TealLabel(None, subroutineL1Label),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_1_subroutine_recursion_v5():
    def sub1Impl(a1):
        return None

    subroutine = SubroutineDefinition(sub1Impl, TealType.uint64)

    subroutineL1Label = LabelReference("l1")
    subroutineOps = [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutineL1Label),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.minus),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutineL1Label),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.retsub),
    ]

    l1Label = LabelReference("l1")
    mainOps = [
        TealOp(None, Op.txn, "Fee"),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bz, l1Label),
        TealOp(None, Op.int, 100),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.return_),
        TealLabel(None, l1Label),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {None: mainOps, subroutine: subroutineOps}

    subroutineGraph = {subroutine: {subroutine}}

    localSlots = {None: set(), subroutine: {0}}

    spillLocalSlotsDuringRecursion(5, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            TealOp(None, Op.txn, "Fee"),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bz, l1Label),
            TealOp(None, Op.int, 100),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.return_),
            TealLabel(None, l1Label),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.return_),
        ],
        subroutine: [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bnz, subroutineL1Label),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.minus),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.swap),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.swap),
            TealOp(None, Op.store, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
            TealOp(None, Op.retsub),
            TealLabel(None, subroutineL1Label),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_multiple_subroutines_no_recursion():
    for version in (4, 5):

        def sub1Impl(a1):
            return None

        def sub2Impl(a1, a2):
            return None

        def sub3Impl(a1, a2, a3):
            return None

        subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
        subroutine2 = SubroutineDefinition(sub1Impl, TealType.uint64)
        subroutine3 = SubroutineDefinition(sub1Impl, TealType.none)

        subroutine1L1Label = LabelReference("l1")
        subroutine1Ops = [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bnz, subroutine1L1Label),
            TealOp(None, Op.err),
            TealLabel(None, subroutine1L1Label),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.callsub, subroutine3),
            TealOp(None, Op.retsub),
        ]

        subroutine2L1Label = LabelReference("l1")
        subroutine2Ops = [
            TealOp(None, Op.store, 1),
            TealOp(None, Op.load, 1),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bnz, subroutine2L1Label),
            TealOp(None, Op.err),
            TealLabel(None, subroutine2L1Label),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.retsub),
        ]

        subroutine3Ops = [
            TealOp(None, Op.retsub),
        ]

        l1Label = LabelReference("l1")
        mainOps = [
            TealOp(None, Op.txn, "Fee"),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bz, l1Label),
            TealOp(None, Op.int, 100),
            TealOp(None, Op.callsub, subroutine1),
            TealOp(None, Op.return_),
            TealLabel(None, l1Label),
            TealOp(None, Op.int, 101),
            TealOp(None, Op.callsub, subroutine2),
            TealOp(None, Op.return_),
        ]

        subroutineMapping = {
            None: mainOps,
            subroutine1: subroutine1Ops,
            subroutine2: subroutine2Ops,
            subroutine3: subroutine3Ops,
        }

        subroutineGraph = {
            subroutine1: {subroutine2},
            subroutine2: set(),
            subroutine3: set(),
        }

        localSlots = {None: set(), subroutine1: {0}, subroutine2: {1}, subroutine3: {}}

        spillLocalSlotsDuringRecursion(
            version, subroutineMapping, subroutineGraph, localSlots
        )

        assert subroutineMapping == {
            None: [
                TealOp(None, Op.txn, "Fee"),
                TealOp(None, Op.int, 0),
                TealOp(None, Op.eq),
                TealOp(None, Op.bz, l1Label),
                TealOp(None, Op.int, 100),
                TealOp(None, Op.callsub, subroutine1),
                TealOp(None, Op.return_),
                TealLabel(None, l1Label),
                TealOp(None, Op.int, 101),
                TealOp(None, Op.callsub, subroutine2),
                TealOp(None, Op.return_),
            ],
            subroutine1: [
                TealOp(None, Op.store, 0),
                TealOp(None, Op.load, 0),
                TealOp(None, Op.int, 0),
                TealOp(None, Op.eq),
                TealOp(None, Op.bnz, subroutine1L1Label),
                TealOp(None, Op.err),
                TealLabel(None, subroutine1L1Label),
                TealOp(None, Op.int, 1),
                TealOp(None, Op.callsub, subroutine3),
                TealOp(None, Op.retsub),
            ],
            subroutine2: [
                TealOp(None, Op.store, 1),
                TealOp(None, Op.load, 1),
                TealOp(None, Op.int, 0),
                TealOp(None, Op.eq),
                TealOp(None, Op.bnz, subroutine2L1Label),
                TealOp(None, Op.err),
                TealLabel(None, subroutine2L1Label),
                TealOp(None, Op.int, 1),
                TealOp(None, Op.retsub),
            ],
            subroutine3: [
                TealOp(None, Op.retsub),
            ],
        }


def test_spillLocalSlotsDuringRecursion_multiple_subroutines_recursion_v4():
    def sub1Impl(a1):
        return None

    def sub2Impl(a1, a2):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine3 = SubroutineDefinition(sub1Impl, TealType.none)

    subroutine1L1Label = LabelReference("l1")
    subroutine1Ops = [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine1L1Label),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.minus),
        TealOp(None, Op.callsub, subroutine1),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutine1L1Label),
        TealOp(None, Op.load, 255),
        TealOp(None, Op.retsub),
    ]

    subroutine2L1Label = LabelReference("l1")
    subroutine2Ops = [
        TealOp(None, Op.store, 1),
        TealOp(None, Op.load, 1),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine2L1Label),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.minus),
        TealOp(None, Op.callsub, subroutine1),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutine2L1Label),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.retsub),
    ]

    subroutine3Ops = [
        TealOp(None, Op.callsub, subroutine3),
        TealOp(None, Op.retsub),
    ]

    l1Label = LabelReference("l1")
    mainOps = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, 255),
        TealOp(None, Op.txn, "Fee"),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bz, l1Label),
        TealOp(None, Op.int, 100),
        TealOp(None, Op.callsub, subroutine1),
        TealOp(None, Op.return_),
        TealLabel(None, l1Label),
        TealOp(None, Op.int, 101),
        TealOp(None, Op.callsub, subroutine2),
        TealOp(None, Op.return_),
        TealOp(None, Op.callsub, subroutine3),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    subroutineGraph = {
        subroutine1: {subroutine1},
        subroutine2: {subroutine1},
        subroutine3: {subroutine3},
    }

    localSlots = {None: set(), subroutine1: {0}, subroutine2: {1}, subroutine3: {}}

    spillLocalSlotsDuringRecursion(4, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            TealOp(None, Op.int, 1),
            TealOp(None, Op.store, 255),
            TealOp(None, Op.txn, "Fee"),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bz, l1Label),
            TealOp(None, Op.int, 100),
            TealOp(None, Op.callsub, subroutine1),
            TealOp(None, Op.return_),
            TealLabel(None, l1Label),
            TealOp(None, Op.int, 101),
            TealOp(None, Op.callsub, subroutine2),
            TealOp(None, Op.return_),
            TealOp(None, Op.callsub, subroutine3),
        ],
        subroutine1: [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bnz, subroutine1L1Label),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.minus),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.dig, 1),
            TealOp(None, Op.callsub, subroutine1),
            TealOp(None, Op.swap),
            TealOp(None, Op.store, 0),
            TealOp(None, Op.swap),
            TealOp(None, Op.pop),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
            TealOp(None, Op.retsub),
            TealLabel(None, subroutine1L1Label),
            TealOp(None, Op.load, 255),
            TealOp(None, Op.retsub),
        ],
        subroutine2: [
            TealOp(None, Op.store, 1),
            TealOp(None, Op.load, 1),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bnz, subroutine2L1Label),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.minus),
            TealOp(None, Op.callsub, subroutine1),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
            TealOp(None, Op.retsub),
            TealLabel(None, subroutine2L1Label),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.retsub),
        ],
        subroutine3: [
            TealOp(None, Op.callsub, subroutine3),
            TealOp(None, Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_multiple_subroutines_recursion_v5():
    def sub1Impl(a1):
        return None

    def sub2Impl(a1, a2):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine3 = SubroutineDefinition(sub1Impl, TealType.none)

    subroutine1L1Label = LabelReference("l1")
    subroutine1Ops = [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine1L1Label),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.minus),
        TealOp(None, Op.callsub, subroutine1),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutine1L1Label),
        TealOp(None, Op.load, 255),
        TealOp(None, Op.retsub),
    ]

    subroutine2L1Label = LabelReference("l1")
    subroutine2Ops = [
        TealOp(None, Op.store, 1),
        TealOp(None, Op.load, 1),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine2L1Label),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.minus),
        TealOp(None, Op.callsub, subroutine1),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutine2L1Label),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.retsub),
    ]

    subroutine3Ops = [
        TealOp(None, Op.callsub, subroutine3),
        TealOp(None, Op.retsub),
    ]

    l1Label = LabelReference("l1")
    mainOps = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, 255),
        TealOp(None, Op.txn, "Fee"),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bz, l1Label),
        TealOp(None, Op.int, 100),
        TealOp(None, Op.callsub, subroutine1),
        TealOp(None, Op.return_),
        TealLabel(None, l1Label),
        TealOp(None, Op.int, 101),
        TealOp(None, Op.callsub, subroutine2),
        TealOp(None, Op.return_),
        TealOp(None, Op.callsub, subroutine3),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    subroutineGraph = {
        subroutine1: {subroutine1},
        subroutine2: {subroutine1},
        subroutine3: {subroutine3},
    }

    localSlots = {None: set(), subroutine1: {0}, subroutine2: {1}, subroutine3: {}}

    spillLocalSlotsDuringRecursion(5, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            TealOp(None, Op.int, 1),
            TealOp(None, Op.store, 255),
            TealOp(None, Op.txn, "Fee"),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bz, l1Label),
            TealOp(None, Op.int, 100),
            TealOp(None, Op.callsub, subroutine1),
            TealOp(None, Op.return_),
            TealLabel(None, l1Label),
            TealOp(None, Op.int, 101),
            TealOp(None, Op.callsub, subroutine2),
            TealOp(None, Op.return_),
            TealOp(None, Op.callsub, subroutine3),
        ],
        subroutine1: [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bnz, subroutine1L1Label),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.minus),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.swap),
            TealOp(None, Op.callsub, subroutine1),
            TealOp(None, Op.swap),
            TealOp(None, Op.store, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
            TealOp(None, Op.retsub),
            TealLabel(None, subroutine1L1Label),
            TealOp(None, Op.load, 255),
            TealOp(None, Op.retsub),
        ],
        subroutine2: [
            TealOp(None, Op.store, 1),
            TealOp(None, Op.load, 1),
            TealOp(None, Op.int, 0),
            TealOp(None, Op.eq),
            TealOp(None, Op.bnz, subroutine2L1Label),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.minus),
            TealOp(None, Op.callsub, subroutine1),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.add),
            TealOp(None, Op.retsub),
            TealLabel(None, subroutine2L1Label),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.retsub),
        ],
        subroutine3: [
            TealOp(None, Op.callsub, subroutine3),
            TealOp(None, Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_many_args_no_return_v4():
    def subImpl(a1, a2, a3):
        return None

    subroutine = SubroutineDefinition(subImpl, TealType.none)

    subroutineOps = [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.store, 1),
        TealOp(None, Op.store, 2),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.retsub),
    ]

    mainOps = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine: subroutineOps,
    }

    subroutineGraph = {
        subroutine: {subroutine},
    }

    localSlots = {None: set(), subroutine: {0, 1, 2}}

    spillLocalSlotsDuringRecursion(4, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.return_),
        ],
        subroutine: [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.store, 2),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.load, 1),
            TealOp(None, Op.load, 2),
            TealOp(None, Op.dig, 5),
            TealOp(None, Op.dig, 5),
            TealOp(None, Op.dig, 5),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.store, 2),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.store, 0),
            TealOp(None, Op.pop),
            TealOp(None, Op.pop),
            TealOp(None, Op.pop),
            TealOp(None, Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_many_args_no_return_v5():
    def subImpl(a1, a2, a3):
        return None

    subroutine = SubroutineDefinition(subImpl, TealType.none)

    subroutineOps = [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.store, 1),
        TealOp(None, Op.store, 2),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.retsub),
    ]

    mainOps = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine: subroutineOps,
    }

    subroutineGraph = {
        subroutine: {subroutine},
    }

    localSlots = {None: set(), subroutine: {0, 1, 2}}

    spillLocalSlotsDuringRecursion(5, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.return_),
        ],
        subroutine: [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.store, 2),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.load, 1),
            TealOp(None, Op.load, 2),
            TealOp(None, Op.uncover, 5),
            TealOp(None, Op.uncover, 5),
            TealOp(None, Op.uncover, 5),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.store, 2),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.store, 0),
            TealOp(None, Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_many_args_return_v4():
    def subImpl(a1, a2, a3):
        return None

    subroutine = SubroutineDefinition(subImpl, TealType.uint64)

    subroutineOps = [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.store, 1),
        TealOp(None, Op.store, 2),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.retsub),
    ]

    mainOps = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine: subroutineOps,
    }

    subroutineGraph = {
        subroutine: {subroutine},
    }

    localSlots = {None: set(), subroutine: {0, 1, 2}}

    spillLocalSlotsDuringRecursion(4, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.return_),
        ],
        subroutine: [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.store, 2),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.load, 1),
            TealOp(None, Op.load, 2),
            TealOp(None, Op.dig, 5),
            TealOp(None, Op.dig, 5),
            TealOp(None, Op.dig, 5),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.store, 0),
            TealOp(None, Op.store, 2),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.swap),
            TealOp(None, Op.store, 0),
            TealOp(None, Op.swap),
            TealOp(None, Op.pop),
            TealOp(None, Op.swap),
            TealOp(None, Op.pop),
            TealOp(None, Op.swap),
            TealOp(None, Op.pop),
            TealOp(None, Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_many_args_return_v5():
    def subImpl(a1, a2, a3):
        return None

    subroutine = SubroutineDefinition(subImpl, TealType.uint64)

    subroutineOps = [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.store, 1),
        TealOp(None, Op.store, 2),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.retsub),
    ]

    mainOps = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine: subroutineOps,
    }

    subroutineGraph = {
        subroutine: {subroutine},
    }

    localSlots = {None: set(), subroutine: {0, 1, 2}}

    spillLocalSlotsDuringRecursion(5, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.return_),
        ],
        subroutine: [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.store, 2),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.load, 1),
            TealOp(None, Op.load, 2),
            TealOp(None, Op.uncover, 5),
            TealOp(None, Op.uncover, 5),
            TealOp(None, Op.uncover, 5),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.cover, 3),
            TealOp(None, Op.store, 2),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.store, 0),
            TealOp(None, Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_more_args_than_slots_v5():
    def subImpl(a1, a2, a3):
        return None

    subroutine = SubroutineDefinition(subImpl, TealType.uint64)

    subroutineOps = [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.store, 1),
        TealOp(None, Op.pop),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.retsub),
    ]

    mainOps = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine: subroutineOps,
    }

    subroutineGraph = {
        subroutine: {subroutine},
    }

    localSlots = {None: set(), subroutine: {0, 1}}

    spillLocalSlotsDuringRecursion(5, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.return_),
        ],
        subroutine: [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.pop),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.cover, 3),
            TealOp(None, Op.load, 1),
            TealOp(None, Op.cover, 3),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.cover, 2),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.store, 0),
            TealOp(None, Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_more_slots_than_args_v5():
    def subImpl(a1, a2, a3):
        return None

    subroutine = SubroutineDefinition(subImpl, TealType.uint64)

    subroutineOps = [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.store, 1),
        TealOp(None, Op.store, 2),
        TealOp(None, Op.int, 10),
        TealOp(None, Op.store, 3),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.retsub),
    ]

    mainOps = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine: subroutineOps,
    }

    subroutineGraph = {
        subroutine: {subroutine},
    }

    localSlots = {None: set(), subroutine: {0, 1, 2, 3}}

    spillLocalSlotsDuringRecursion(5, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.return_),
        ],
        subroutine: [
            TealOp(None, Op.store, 0),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.store, 2),
            TealOp(None, Op.int, 10),
            TealOp(None, Op.store, 3),
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.load, 0),
            TealOp(None, Op.load, 1),
            TealOp(None, Op.load, 2),
            TealOp(None, Op.load, 3),
            TealOp(None, Op.uncover, 6),
            TealOp(None, Op.uncover, 6),
            TealOp(None, Op.uncover, 6),
            TealOp(None, Op.callsub, subroutine),
            TealOp(None, Op.cover, 4),
            TealOp(None, Op.store, 3),
            TealOp(None, Op.store, 2),
            TealOp(None, Op.store, 1),
            TealOp(None, Op.store, 0),
            TealOp(None, Op.retsub),
        ],
    }


def test_resolveSubroutines():
    def sub1Impl(a1):
        return None

    def sub2Impl(a1, a2):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine3 = SubroutineDefinition(sub1Impl, TealType.none)

    subroutine1L1Label = LabelReference("l1")
    subroutine1Ops = [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine1L1Label),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.minus),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.dig, 1),
        TealOp(None, Op.callsub, subroutine1),
        TealOp(None, Op.swap),
        TealOp(None, Op.store, 0),
        TealOp(None, Op.swap),
        TealOp(None, Op.pop),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutine1L1Label),
        TealOp(None, Op.load, 255),
        TealOp(None, Op.retsub),
    ]

    subroutine2L1Label = LabelReference("l1")
    subroutine2Ops = [
        TealOp(None, Op.store, 1),
        TealOp(None, Op.load, 1),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine2L1Label),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.minus),
        TealOp(None, Op.callsub, subroutine1),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutine2L1Label),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.retsub),
    ]

    subroutine3Ops = [
        TealOp(None, Op.callsub, subroutine3),
        TealOp(None, Op.retsub),
    ]

    l1Label = LabelReference("l1")
    mainOps = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, 255),
        TealOp(None, Op.txn, "Fee"),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bz, l1Label),
        TealOp(None, Op.int, 100),
        TealOp(None, Op.callsub, subroutine1),
        TealOp(None, Op.return_),
        TealLabel(None, l1Label),
        TealOp(None, Op.int, 101),
        TealOp(None, Op.callsub, subroutine2),
        TealOp(None, Op.return_),
        TealOp(None, Op.callsub, subroutine3),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    expected = OrderedDict()
    expected[subroutine1] = "sub0"
    expected[subroutine2] = "sub1"
    expected[subroutine3] = "sub2"

    actual = resolveSubroutines(subroutineMapping)
    assert actual == expected

    assert mainOps == [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.store, 255),
        TealOp(None, Op.txn, "Fee"),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bz, l1Label),
        TealOp(None, Op.int, 100),
        TealOp(None, Op.callsub, expected[subroutine1]),
        TealOp(None, Op.return_),
        TealLabel(None, l1Label),
        TealOp(None, Op.int, 101),
        TealOp(None, Op.callsub, expected[subroutine2]),
        TealOp(None, Op.return_),
        TealOp(None, Op.callsub, expected[subroutine3]),
    ]

    assert subroutine1Ops == [
        TealOp(None, Op.store, 0),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine1L1Label),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.minus),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.dig, 1),
        TealOp(None, Op.callsub, expected[subroutine1]),
        TealOp(None, Op.swap),
        TealOp(None, Op.store, 0),
        TealOp(None, Op.swap),
        TealOp(None, Op.pop),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutine1L1Label),
        TealOp(None, Op.load, 255),
        TealOp(None, Op.retsub),
    ]

    assert subroutine2Ops == [
        TealOp(None, Op.store, 1),
        TealOp(None, Op.load, 1),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine2L1Label),
        TealOp(None, Op.load, 0),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.minus),
        TealOp(None, Op.callsub, expected[subroutine1]),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutine2L1Label),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.retsub),
    ]

    assert subroutine3Ops == [
        TealOp(None, Op.callsub, expected[subroutine3]),
        TealOp(None, Op.retsub),
    ]
