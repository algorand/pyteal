from collections import OrderedDict

import pytest

import pyteal as pt

from pyteal.compiler.subroutines import (
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

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.bytes)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

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

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.bytes)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

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

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.bytes)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

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

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.bytes)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

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
        l1Label = pt.LabelReference("l1")
        mainOps = [
            pt.TealOp(None, pt.Op.txn, "Fee"),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bz, l1Label),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.return_),
            pt.TealLabel(None, l1Label),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.return_),
        ]

        subroutineMapping = {None: mainOps}

        subroutineGraph = dict()

        localSlots = {None: set()}

        spillLocalSlotsDuringRecursion(
            version, subroutineMapping, subroutineGraph, localSlots
        )

        assert mainOps == [
            pt.TealOp(None, pt.Op.txn, "Fee"),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bz, l1Label),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.return_),
            pt.TealLabel(None, l1Label),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.return_),
        ]


def test_spillLocalSlotsDuringRecursion_1_subroutine_no_recursion():
    for version in (4, 5):
        subroutine = pt.SubroutineDefinition(lambda: None, pt.TealType.uint64)

        subroutineL1Label = pt.LabelReference("l1")
        subroutineOps = [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bnz, subroutineL1Label),
            pt.TealOp(None, pt.Op.err),
            pt.TealLabel(None, subroutineL1Label),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.retsub),
        ]

        l1Label = pt.LabelReference("l1")
        mainOps = [
            pt.TealOp(None, pt.Op.txn, "Fee"),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bz, l1Label),
            pt.TealOp(None, pt.Op.int, 100),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.return_),
            pt.TealLabel(None, l1Label),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.return_),
        ]

        subroutineMapping = {None: mainOps, subroutine: subroutineOps}

        subroutineGraph = {subroutine: set()}

        localSlots = {None: set(), subroutine: {0}}

        spillLocalSlotsDuringRecursion(
            version, subroutineMapping, subroutineGraph, localSlots
        )

        assert subroutineMapping == {
            None: [
                pt.TealOp(None, pt.Op.txn, "Fee"),
                pt.TealOp(None, pt.Op.int, 0),
                pt.TealOp(None, pt.Op.eq),
                pt.TealOp(None, pt.Op.bz, l1Label),
                pt.TealOp(None, pt.Op.int, 100),
                pt.TealOp(None, pt.Op.callsub, subroutine),
                pt.TealOp(None, pt.Op.return_),
                pt.TealLabel(None, l1Label),
                pt.TealOp(None, pt.Op.int, 0),
                pt.TealOp(None, pt.Op.return_),
            ],
            subroutine: [
                pt.TealOp(None, pt.Op.store, 0),
                pt.TealOp(None, pt.Op.load, 0),
                pt.TealOp(None, pt.Op.int, 0),
                pt.TealOp(None, pt.Op.eq),
                pt.TealOp(None, pt.Op.bnz, subroutineL1Label),
                pt.TealOp(None, pt.Op.err),
                pt.TealLabel(None, subroutineL1Label),
                pt.TealOp(None, pt.Op.int, 1),
                pt.TealOp(None, pt.Op.retsub),
            ],
        }


def test_spillLocalSlotsDuringRecursion_1_subroutine_recursion_v4():
    def sub1Impl(a1):
        return None

    subroutine = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)

    subroutineL1Label = pt.LabelReference("l1")
    subroutineOps = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutineL1Label),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.minus),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutineL1Label),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    l1Label = pt.LabelReference("l1")
    mainOps = [
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, l1Label),
        pt.TealOp(None, pt.Op.int, 100),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, l1Label),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.return_),
    ]

    subroutineMapping = {None: mainOps, subroutine: subroutineOps}

    subroutineGraph = {subroutine: {subroutine}}

    localSlots = {None: set(), subroutine: {0}}

    spillLocalSlotsDuringRecursion(4, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            pt.TealOp(None, pt.Op.txn, "Fee"),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bz, l1Label),
            pt.TealOp(None, pt.Op.int, 100),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.return_),
            pt.TealLabel(None, l1Label),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.return_),
        ],
        subroutine: [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bnz, subroutineL1Label),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.minus),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.dig, 1),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.pop),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.add),
            pt.TealOp(None, pt.Op.retsub),
            pt.TealLabel(None, subroutineL1Label),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_1_subroutine_recursion_v5():
    def sub1Impl(a1):
        return None

    subroutine = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)

    subroutineL1Label = pt.LabelReference("l1")
    subroutineOps = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutineL1Label),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.minus),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutineL1Label),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    l1Label = pt.LabelReference("l1")
    mainOps = [
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, l1Label),
        pt.TealOp(None, pt.Op.int, 100),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, l1Label),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.return_),
    ]

    subroutineMapping = {None: mainOps, subroutine: subroutineOps}

    subroutineGraph = {subroutine: {subroutine}}

    localSlots = {None: set(), subroutine: {0}}

    spillLocalSlotsDuringRecursion(5, subroutineMapping, subroutineGraph, localSlots)

    assert subroutineMapping == {
        None: [
            pt.TealOp(None, pt.Op.txn, "Fee"),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bz, l1Label),
            pt.TealOp(None, pt.Op.int, 100),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.return_),
            pt.TealLabel(None, l1Label),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.return_),
        ],
        subroutine: [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bnz, subroutineL1Label),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.minus),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.add),
            pt.TealOp(None, pt.Op.retsub),
            pt.TealLabel(None, subroutineL1Label),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.retsub),
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

        subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
        subroutine2 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
        subroutine3 = pt.SubroutineDefinition(sub1Impl, pt.TealType.none)

        subroutine1L1Label = pt.LabelReference("l1")
        subroutine1Ops = [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bnz, subroutine1L1Label),
            pt.TealOp(None, pt.Op.err),
            pt.TealLabel(None, subroutine1L1Label),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.callsub, subroutine3),
            pt.TealOp(None, pt.Op.retsub),
        ]

        subroutine2L1Label = pt.LabelReference("l1")
        subroutine2Ops = [
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.load, 1),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bnz, subroutine2L1Label),
            pt.TealOp(None, pt.Op.err),
            pt.TealLabel(None, subroutine2L1Label),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.retsub),
        ]

        subroutine3Ops = [
            pt.TealOp(None, pt.Op.retsub),
        ]

        l1Label = pt.LabelReference("l1")
        mainOps = [
            pt.TealOp(None, pt.Op.txn, "Fee"),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bz, l1Label),
            pt.TealOp(None, pt.Op.int, 100),
            pt.TealOp(None, pt.Op.callsub, subroutine1),
            pt.TealOp(None, pt.Op.return_),
            pt.TealLabel(None, l1Label),
            pt.TealOp(None, pt.Op.int, 101),
            pt.TealOp(None, pt.Op.callsub, subroutine2),
            pt.TealOp(None, pt.Op.return_),
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
                pt.TealOp(None, pt.Op.txn, "Fee"),
                pt.TealOp(None, pt.Op.int, 0),
                pt.TealOp(None, pt.Op.eq),
                pt.TealOp(None, pt.Op.bz, l1Label),
                pt.TealOp(None, pt.Op.int, 100),
                pt.TealOp(None, pt.Op.callsub, subroutine1),
                pt.TealOp(None, pt.Op.return_),
                pt.TealLabel(None, l1Label),
                pt.TealOp(None, pt.Op.int, 101),
                pt.TealOp(None, pt.Op.callsub, subroutine2),
                pt.TealOp(None, pt.Op.return_),
            ],
            subroutine1: [
                pt.TealOp(None, pt.Op.store, 0),
                pt.TealOp(None, pt.Op.load, 0),
                pt.TealOp(None, pt.Op.int, 0),
                pt.TealOp(None, pt.Op.eq),
                pt.TealOp(None, pt.Op.bnz, subroutine1L1Label),
                pt.TealOp(None, pt.Op.err),
                pt.TealLabel(None, subroutine1L1Label),
                pt.TealOp(None, pt.Op.int, 1),
                pt.TealOp(None, pt.Op.callsub, subroutine3),
                pt.TealOp(None, pt.Op.retsub),
            ],
            subroutine2: [
                pt.TealOp(None, pt.Op.store, 1),
                pt.TealOp(None, pt.Op.load, 1),
                pt.TealOp(None, pt.Op.int, 0),
                pt.TealOp(None, pt.Op.eq),
                pt.TealOp(None, pt.Op.bnz, subroutine2L1Label),
                pt.TealOp(None, pt.Op.err),
                pt.TealLabel(None, subroutine2L1Label),
                pt.TealOp(None, pt.Op.int, 1),
                pt.TealOp(None, pt.Op.retsub),
            ],
            subroutine3: [
                pt.TealOp(None, pt.Op.retsub),
            ],
        }


def test_spillLocalSlotsDuringRecursion_multiple_subroutines_recursion_v4():
    def sub1Impl(a1):
        return None

    def sub2Impl(a1, a2):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine3 = pt.SubroutineDefinition(sub1Impl, pt.TealType.none)

    subroutine1L1Label = pt.LabelReference("l1")
    subroutine1Ops = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine1L1Label),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.minus),
        pt.TealOp(None, pt.Op.callsub, subroutine1),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutine1L1Label),
        pt.TealOp(None, pt.Op.load, 255),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine2L1Label = pt.LabelReference("l1")
    subroutine2Ops = [
        pt.TealOp(None, pt.Op.store, 1),
        pt.TealOp(None, pt.Op.load, 1),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine2L1Label),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.minus),
        pt.TealOp(None, pt.Op.callsub, subroutine1),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutine2L1Label),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine3Ops = [
        pt.TealOp(None, pt.Op.callsub, subroutine3),
        pt.TealOp(None, pt.Op.retsub),
    ]

    l1Label = pt.LabelReference("l1")
    mainOps = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, 255),
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, l1Label),
        pt.TealOp(None, pt.Op.int, 100),
        pt.TealOp(None, pt.Op.callsub, subroutine1),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, l1Label),
        pt.TealOp(None, pt.Op.int, 101),
        pt.TealOp(None, pt.Op.callsub, subroutine2),
        pt.TealOp(None, pt.Op.return_),
        pt.TealOp(None, pt.Op.callsub, subroutine3),
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
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.store, 255),
            pt.TealOp(None, pt.Op.txn, "Fee"),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bz, l1Label),
            pt.TealOp(None, pt.Op.int, 100),
            pt.TealOp(None, pt.Op.callsub, subroutine1),
            pt.TealOp(None, pt.Op.return_),
            pt.TealLabel(None, l1Label),
            pt.TealOp(None, pt.Op.int, 101),
            pt.TealOp(None, pt.Op.callsub, subroutine2),
            pt.TealOp(None, pt.Op.return_),
            pt.TealOp(None, pt.Op.callsub, subroutine3),
        ],
        subroutine1: [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bnz, subroutine1L1Label),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.minus),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.dig, 1),
            pt.TealOp(None, pt.Op.callsub, subroutine1),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.pop),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.add),
            pt.TealOp(None, pt.Op.retsub),
            pt.TealLabel(None, subroutine1L1Label),
            pt.TealOp(None, pt.Op.load, 255),
            pt.TealOp(None, pt.Op.retsub),
        ],
        subroutine2: [
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.load, 1),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bnz, subroutine2L1Label),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.minus),
            pt.TealOp(None, pt.Op.callsub, subroutine1),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.add),
            pt.TealOp(None, pt.Op.retsub),
            pt.TealLabel(None, subroutine2L1Label),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.retsub),
        ],
        subroutine3: [
            pt.TealOp(None, pt.Op.callsub, subroutine3),
            pt.TealOp(None, pt.Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_multiple_subroutines_recursion_v5():
    def sub1Impl(a1):
        return None

    def sub2Impl(a1, a2):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine3 = pt.SubroutineDefinition(sub1Impl, pt.TealType.none)

    subroutine1L1Label = pt.LabelReference("l1")
    subroutine1Ops = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine1L1Label),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.minus),
        pt.TealOp(None, pt.Op.callsub, subroutine1),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutine1L1Label),
        pt.TealOp(None, pt.Op.load, 255),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine2L1Label = pt.LabelReference("l1")
    subroutine2Ops = [
        pt.TealOp(None, pt.Op.store, 1),
        pt.TealOp(None, pt.Op.load, 1),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine2L1Label),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.minus),
        pt.TealOp(None, pt.Op.callsub, subroutine1),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutine2L1Label),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine3Ops = [
        pt.TealOp(None, pt.Op.callsub, subroutine3),
        pt.TealOp(None, pt.Op.retsub),
    ]

    l1Label = pt.LabelReference("l1")
    mainOps = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, 255),
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, l1Label),
        pt.TealOp(None, pt.Op.int, 100),
        pt.TealOp(None, pt.Op.callsub, subroutine1),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, l1Label),
        pt.TealOp(None, pt.Op.int, 101),
        pt.TealOp(None, pt.Op.callsub, subroutine2),
        pt.TealOp(None, pt.Op.return_),
        pt.TealOp(None, pt.Op.callsub, subroutine3),
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
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.store, 255),
            pt.TealOp(None, pt.Op.txn, "Fee"),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bz, l1Label),
            pt.TealOp(None, pt.Op.int, 100),
            pt.TealOp(None, pt.Op.callsub, subroutine1),
            pt.TealOp(None, pt.Op.return_),
            pt.TealLabel(None, l1Label),
            pt.TealOp(None, pt.Op.int, 101),
            pt.TealOp(None, pt.Op.callsub, subroutine2),
            pt.TealOp(None, pt.Op.return_),
            pt.TealOp(None, pt.Op.callsub, subroutine3),
        ],
        subroutine1: [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bnz, subroutine1L1Label),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.minus),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.callsub, subroutine1),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.add),
            pt.TealOp(None, pt.Op.retsub),
            pt.TealLabel(None, subroutine1L1Label),
            pt.TealOp(None, pt.Op.load, 255),
            pt.TealOp(None, pt.Op.retsub),
        ],
        subroutine2: [
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.load, 1),
            pt.TealOp(None, pt.Op.int, 0),
            pt.TealOp(None, pt.Op.eq),
            pt.TealOp(None, pt.Op.bnz, subroutine2L1Label),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.minus),
            pt.TealOp(None, pt.Op.callsub, subroutine1),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.add),
            pt.TealOp(None, pt.Op.retsub),
            pt.TealLabel(None, subroutine2L1Label),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.retsub),
        ],
        subroutine3: [
            pt.TealOp(None, pt.Op.callsub, subroutine3),
            pt.TealOp(None, pt.Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_many_args_no_return_v4():
    def subImpl(a1, a2, a3):
        return None

    subroutine = pt.SubroutineDefinition(subImpl, pt.TealType.none)

    subroutineOps = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.store, 1),
        pt.TealOp(None, pt.Op.store, 2),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.retsub),
    ]

    mainOps = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.return_),
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
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.return_),
        ],
        subroutine: [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.store, 2),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.load, 1),
            pt.TealOp(None, pt.Op.load, 2),
            pt.TealOp(None, pt.Op.dig, 5),
            pt.TealOp(None, pt.Op.dig, 5),
            pt.TealOp(None, pt.Op.dig, 5),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.store, 2),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.pop),
            pt.TealOp(None, pt.Op.pop),
            pt.TealOp(None, pt.Op.pop),
            pt.TealOp(None, pt.Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_many_args_no_return_v5():
    def subImpl(a1, a2, a3):
        return None

    subroutine = pt.SubroutineDefinition(subImpl, pt.TealType.none)

    subroutineOps = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.store, 1),
        pt.TealOp(None, pt.Op.store, 2),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.retsub),
    ]

    mainOps = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.return_),
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
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.return_),
        ],
        subroutine: [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.store, 2),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.load, 1),
            pt.TealOp(None, pt.Op.load, 2),
            pt.TealOp(None, pt.Op.uncover, 5),
            pt.TealOp(None, pt.Op.uncover, 5),
            pt.TealOp(None, pt.Op.uncover, 5),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.store, 2),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_many_args_return_v4():
    def subImpl(a1, a2, a3):
        return None

    subroutine = pt.SubroutineDefinition(subImpl, pt.TealType.uint64)

    subroutineOps = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.store, 1),
        pt.TealOp(None, pt.Op.store, 2),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.retsub),
    ]

    mainOps = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.return_),
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
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.return_),
        ],
        subroutine: [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.store, 2),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.load, 1),
            pt.TealOp(None, pt.Op.load, 2),
            pt.TealOp(None, pt.Op.dig, 5),
            pt.TealOp(None, pt.Op.dig, 5),
            pt.TealOp(None, pt.Op.dig, 5),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.store, 2),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.pop),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.pop),
            pt.TealOp(None, pt.Op.swap),
            pt.TealOp(None, pt.Op.pop),
            pt.TealOp(None, pt.Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_many_args_return_v5():
    def subImpl(a1, a2, a3):
        return None

    subroutine = pt.SubroutineDefinition(subImpl, pt.TealType.uint64)

    subroutineOps = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.store, 1),
        pt.TealOp(None, pt.Op.store, 2),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.retsub),
    ]

    mainOps = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.return_),
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
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.return_),
        ],
        subroutine: [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.store, 2),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.load, 1),
            pt.TealOp(None, pt.Op.load, 2),
            pt.TealOp(None, pt.Op.uncover, 5),
            pt.TealOp(None, pt.Op.uncover, 5),
            pt.TealOp(None, pt.Op.uncover, 5),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.cover, 3),
            pt.TealOp(None, pt.Op.store, 2),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_more_args_than_slots_v5():
    def subImpl(a1, a2, a3):
        return None

    subroutine = pt.SubroutineDefinition(subImpl, pt.TealType.uint64)

    subroutineOps = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.store, 1),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.retsub),
    ]

    mainOps = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.return_),
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
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.return_),
        ],
        subroutine: [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.pop),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.cover, 3),
            pt.TealOp(None, pt.Op.load, 1),
            pt.TealOp(None, pt.Op.cover, 3),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.cover, 2),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_more_slots_than_args_v5():
    def subImpl(a1, a2, a3):
        return None

    subroutine = pt.SubroutineDefinition(subImpl, pt.TealType.uint64)

    subroutineOps = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.store, 1),
        pt.TealOp(None, pt.Op.store, 2),
        pt.TealOp(None, pt.Op.int, 10),
        pt.TealOp(None, pt.Op.store, 3),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.retsub),
    ]

    mainOps = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine),
        pt.TealOp(None, pt.Op.return_),
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
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.return_),
        ],
        subroutine: [
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.store, 2),
            pt.TealOp(None, pt.Op.int, 10),
            pt.TealOp(None, pt.Op.store, 3),
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.load, 0),
            pt.TealOp(None, pt.Op.load, 1),
            pt.TealOp(None, pt.Op.load, 2),
            pt.TealOp(None, pt.Op.load, 3),
            pt.TealOp(None, pt.Op.uncover, 6),
            pt.TealOp(None, pt.Op.uncover, 6),
            pt.TealOp(None, pt.Op.uncover, 6),
            pt.TealOp(None, pt.Op.callsub, subroutine),
            pt.TealOp(None, pt.Op.cover, 4),
            pt.TealOp(None, pt.Op.store, 3),
            pt.TealOp(None, pt.Op.store, 2),
            pt.TealOp(None, pt.Op.store, 1),
            pt.TealOp(None, pt.Op.store, 0),
            pt.TealOp(None, pt.Op.retsub),
        ],
    }


def test_spillLocalSlotsDuringRecursion_recursive_with_scratchvar():
    # modifying test_spillLocalSlotsDuringRecursion_multiple_subroutines_no_recursion()
    # to be recursive and fail due to by-ref args
    def sub1Impl(a1):
        return None

    def sub2Impl(a1, a2: pt.ScratchVar):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.uint64)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

    subroutine1L1Label = pt.LabelReference("l1")
    subroutine1Ops = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine1L1Label),
        pt.TealOp(None, pt.Op.err),
        pt.TealLabel(None, subroutine1L1Label),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.callsub, subroutine3),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine2L1Label = pt.LabelReference("l1")
    subroutine2Ops = [
        pt.TealOp(None, pt.Op.store, 1),
        pt.TealOp(None, pt.Op.load, 1),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine2L1Label),
        pt.TealOp(None, pt.Op.err),
        pt.TealLabel(None, subroutine2L1Label),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine3Ops = [
        pt.TealOp(None, pt.Op.retsub),
    ]

    l1Label = pt.LabelReference("l1")
    mainOps = [
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, l1Label),
        pt.TealOp(None, pt.Op.int, 100),
        pt.TealOp(None, pt.Op.callsub, subroutine1),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, l1Label),
        pt.TealOp(None, pt.Op.int, 101),
        pt.TealOp(None, pt.Op.callsub, subroutine2),
        pt.TealOp(None, pt.Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    subroutineGraph = {
        subroutine1: {subroutine2},
        subroutine2: {subroutine1},
        subroutine3: set(),
    }

    localSlots = {None: set(), subroutine1: {0}, subroutine2: {1}, subroutine3: {}}

    with pytest.raises(pt.TealInputError) as tie:
        spillLocalSlotsDuringRecursion(
            5, subroutineMapping, subroutineGraph, localSlots
        )

    assert (
        "ScratchVar arguments not allowed in recursive subroutines, but a recursive call-path was detected: sub2Impl()-->sub1Impl()-->sub2Impl()"
        in str(tie)
    )


def test_resolveSubroutines():
    def sub1Impl(a1):
        return None

    def sub2Impl(a1, a2):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.uint64)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

    subroutine1L1Label = pt.LabelReference("l1")
    subroutine1Ops = [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine1L1Label),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.minus),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.dig, 1),
        pt.TealOp(None, pt.Op.callsub, subroutine1),
        pt.TealOp(None, pt.Op.swap),
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.swap),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutine1L1Label),
        pt.TealOp(None, pt.Op.load, 255),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine2L1Label = pt.LabelReference("l1")
    subroutine2Ops = [
        pt.TealOp(None, pt.Op.store, 1),
        pt.TealOp(None, pt.Op.load, 1),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine2L1Label),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.minus),
        pt.TealOp(None, pt.Op.callsub, subroutine1),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutine2L1Label),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine3Ops = [
        pt.TealOp(None, pt.Op.callsub, subroutine3),
        pt.TealOp(None, pt.Op.retsub),
    ]

    l1Label = pt.LabelReference("l1")
    mainOps = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, 255),
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, l1Label),
        pt.TealOp(None, pt.Op.int, 100),
        pt.TealOp(None, pt.Op.callsub, subroutine1),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, l1Label),
        pt.TealOp(None, pt.Op.int, 101),
        pt.TealOp(None, pt.Op.callsub, subroutine2),
        pt.TealOp(None, pt.Op.return_),
        pt.TealOp(None, pt.Op.callsub, subroutine3),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    expected = OrderedDict()
    expected[subroutine1] = "sub1Impl_0"
    expected[subroutine2] = "sub2Impl_1"
    expected[subroutine3] = "sub3Impl_2"

    actual = resolveSubroutines(subroutineMapping)
    assert actual == expected

    assert mainOps == [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.store, 255),
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, l1Label),
        pt.TealOp(None, pt.Op.int, 100),
        pt.TealOp(None, pt.Op.callsub, expected[subroutine1]),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, l1Label),
        pt.TealOp(None, pt.Op.int, 101),
        pt.TealOp(None, pt.Op.callsub, expected[subroutine2]),
        pt.TealOp(None, pt.Op.return_),
        pt.TealOp(None, pt.Op.callsub, expected[subroutine3]),
    ]

    assert subroutine1Ops == [
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine1L1Label),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.minus),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.dig, 1),
        pt.TealOp(None, pt.Op.callsub, expected[subroutine1]),
        pt.TealOp(None, pt.Op.swap),
        pt.TealOp(None, pt.Op.store, 0),
        pt.TealOp(None, pt.Op.swap),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutine1L1Label),
        pt.TealOp(None, pt.Op.load, 255),
        pt.TealOp(None, pt.Op.retsub),
    ]

    assert subroutine2Ops == [
        pt.TealOp(None, pt.Op.store, 1),
        pt.TealOp(None, pt.Op.load, 1),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine2L1Label),
        pt.TealOp(None, pt.Op.load, 0),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.minus),
        pt.TealOp(None, pt.Op.callsub, expected[subroutine1]),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutine2L1Label),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.retsub),
    ]

    assert subroutine3Ops == [
        pt.TealOp(None, pt.Op.callsub, expected[subroutine3]),
        pt.TealOp(None, pt.Op.retsub),
    ]
