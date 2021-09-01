from collections import OrderedDict

from .. import *

# this is not necessary but mypy complains if it's not included
from ..ast import *

from .flatten import flattenBlocks, flattenSubroutines


def test_flattenBlocks_none():
    blocks = []

    expected = []
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_single_empty():
    blocks = [TealSimpleBlock([])]

    expected = []
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_single_one():
    blocks = [TealSimpleBlock([TealOp(None, Op.int, 1)])]

    expected = [TealOp(None, Op.int, 1)]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_single_many():
    blocks = [
        TealSimpleBlock(
            [
                TealOp(None, Op.int, 1),
                TealOp(None, Op.int, 2),
                TealOp(None, Op.int, 3),
                TealOp(None, Op.add),
                TealOp(None, Op.add),
            ]
        )
    ]

    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
        TealOp(None, Op.add),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_sequence():
    block5 = TealSimpleBlock([TealOp(None, Op.int, 5)])
    block4 = TealSimpleBlock([TealOp(None, Op.int, 4)])
    block4.setNextBlock(block5)
    block3 = TealSimpleBlock([TealOp(None, Op.int, 3)])
    block3.setNextBlock(block4)
    block2 = TealSimpleBlock([TealOp(None, Op.int, 2)])
    block2.setNextBlock(block3)
    block1 = TealSimpleBlock([TealOp(None, Op.int, 1)])
    block1.setNextBlock(block2)
    block1.addIncoming()
    block1.validateTree()
    blocks = [block1, block2, block3, block4, block5]

    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.int, 4),
        TealOp(None, Op.int, 5),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_branch():
    blockTrue = TealSimpleBlock(
        [TealOp(None, Op.byte, '"true"'), TealOp(None, Op.return_)]
    )
    blockFalse = TealSimpleBlock(
        [TealOp(None, Op.byte, '"false"'), TealOp(None, Op.return_)]
    )
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [block, blockFalse, blockTrue]

    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.bnz, LabelReference("l2")),
        TealOp(None, Op.byte, '"false"'),
        TealOp(None, Op.return_),
        TealLabel(None, LabelReference("l2")),
        TealOp(None, Op.byte, '"true"'),
        TealOp(None, Op.return_),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_branch_equal_end_nodes():
    blockTrueEnd = TealSimpleBlock([TealOp(None, Op.return_)])
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueEnd)
    blockFalseEnd = TealSimpleBlock([TealOp(None, Op.return_)])
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    blockFalse.setNextBlock(blockFalseEnd)
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [block, blockFalse, blockFalseEnd, blockTrue, blockTrueEnd]

    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.bnz, LabelReference("l3")),
        TealOp(None, Op.byte, '"false"'),
        TealOp(None, Op.return_),
        TealLabel(None, LabelReference("l3")),
        TealOp(None, Op.byte, '"true"'),
        TealOp(None, Op.return_),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_branch_converge():
    blockEnd = TealSimpleBlock([TealOp(None, Op.return_)])
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true"')])
    blockTrue.setNextBlock(blockEnd)
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    blockFalse.setNextBlock(blockEnd)
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [block, blockFalse, blockTrue, blockEnd]

    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.bnz, LabelReference("l2")),
        TealOp(None, Op.byte, '"false"'),
        TealOp(None, Op.b, LabelReference("l3")),
        TealLabel(None, LabelReference("l2")),
        TealOp(None, Op.byte, '"true"'),
        TealLabel(None, LabelReference("l3")),
        TealOp(None, Op.return_),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_multiple_branch():
    blockTrueTrue = TealSimpleBlock(
        [TealOp(None, Op.byte, '"true true"'), TealOp(None, Op.return_)]
    )
    blockTrueFalse = TealSimpleBlock(
        [TealOp(None, Op.byte, '"true false"'), TealOp(None, Op.err)]
    )
    blockTrueBranch = TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = TealSimpleBlock(
        [TealOp(None, Op.byte, '"false"'), TealOp(None, Op.return_)]
    )
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [
        block,
        blockFalse,
        blockTrue,
        blockTrueBranch,
        blockTrueFalse,
        blockTrueTrue,
    ]

    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.bnz, LabelReference("l2")),
        TealOp(None, Op.byte, '"false"'),
        TealOp(None, Op.return_),
        TealLabel(None, LabelReference("l2")),
        TealOp(None, Op.byte, '"true"'),
        TealOp(None, Op.bnz, LabelReference("l5")),
        TealOp(None, Op.byte, '"true false"'),
        TealOp(None, Op.err),
        TealLabel(None, LabelReference("l5")),
        TealOp(None, Op.byte, '"true true"'),
        TealOp(None, Op.return_),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_multiple_branch_converge():
    blockEnd = TealSimpleBlock([TealOp(None, Op.return_)])
    blockTrueTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true true"')])
    blockTrueTrue.setNextBlock(blockEnd)
    blockTrueFalse = TealSimpleBlock(
        [TealOp(None, Op.byte, '"true false"'), TealOp(None, Op.err)]
    )
    blockTrueBranch = TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    blockFalse.setNextBlock(blockEnd)
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [
        block,
        blockFalse,
        blockTrue,
        blockTrueBranch,
        blockTrueFalse,
        blockTrueTrue,
        blockEnd,
    ]

    expected = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.bnz, LabelReference("l2")),
        TealOp(None, Op.byte, '"false"'),
        TealOp(None, Op.b, LabelReference("l6")),
        TealLabel(None, LabelReference("l2")),
        TealOp(None, Op.byte, '"true"'),
        TealOp(None, Op.bnz, LabelReference("l5")),
        TealOp(None, Op.byte, '"true false"'),
        TealOp(None, Op.err),
        TealLabel(None, LabelReference("l5")),
        TealOp(None, Op.byte, '"true true"'),
        TealLabel(None, LabelReference("l6")),
        TealOp(None, Op.return_),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenSubroutines_no_subroutines():
    subroutineToLabel = OrderedDict()

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

    expectedL1Label = LabelReference("main_l1")
    expected = [
        TealOp(None, Op.txn, "Fee"),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bz, expectedL1Label),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.return_),
        TealLabel(None, expectedL1Label),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.return_),
    ]

    actual = flattenSubroutines(subroutineMapping, subroutineToLabel)

    assert actual == expected


def test_flattenSubroutines_1_subroutine():
    subroutine = SubroutineDefinition(lambda: Int(1) + Int(2) + Int(3), TealType.uint64)

    subroutineToLabel = OrderedDict()
    subroutineToLabel[subroutine] = "sub0"

    subroutineLabel = LabelReference(subroutineToLabel[subroutine])
    subroutineOps = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
    ]

    l1Label = LabelReference("l1")
    mainOps = [
        TealOp(None, Op.txn, "Fee"),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bz, l1Label),
        TealOp(None, Op.callsub, subroutineLabel),
        TealOp(None, Op.return_),
        TealLabel(None, l1Label),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {None: mainOps, subroutine: subroutineOps}

    expectedL1Label = LabelReference("main_l1")
    expectedSubroutineLabel = LabelReference("sub0")
    expected = [
        TealOp(None, Op.txn, "Fee"),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bz, expectedL1Label),
        TealOp(None, Op.callsub, expectedSubroutineLabel),
        TealOp(None, Op.return_),
        TealLabel(None, expectedL1Label),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.return_),
        TealLabel(None, expectedSubroutineLabel, "<lambda>"),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
    ]

    actual = flattenSubroutines(subroutineMapping, subroutineToLabel)

    assert actual == expected


def test_flattenSubroutines_multiple_subroutines():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = SubroutineDefinition(sub1Impl, TealType.uint64)
    subroutine2 = SubroutineDefinition(sub2Impl, TealType.bytes)
    subroutine3 = SubroutineDefinition(sub3Impl, TealType.none)

    subroutineToLabel = OrderedDict()
    subroutineToLabel[subroutine1] = "sub0"
    subroutineToLabel[subroutine2] = "sub1"
    subroutineToLabel[subroutine3] = "sub2"

    subroutine1Label = LabelReference(subroutineToLabel[subroutine1])
    subroutine1Ops = [
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
    ]

    subroutine2Label = LabelReference(subroutineToLabel[subroutine2])
    subroutine2L1Label = LabelReference("l1")
    subroutine2L2Label = LabelReference("l2")
    subroutine2L3Label = LabelReference("l3")
    subroutine2L4Label = LabelReference("l4")
    subroutine2Ops = [
        TealOp(None, Op.dup),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine2L1Label),
        TealOp(None, Op.dup),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine2L2Label),
        TealOp(None, Op.dup),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine2L3Label),
        TealOp(None, Op.dup),
        TealOp(None, Op.int, 4),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, subroutine2L4Label),
        TealOp(None, Op.err),
        TealLabel(None, subroutine2L1Label),
        TealOp(None, Op.pop),
        TealOp(None, Op.byte, '"1"'),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutine2L2Label),
        TealOp(None, Op.pop),
        TealOp(None, Op.byte, '"2"'),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutine2L3Label),
        TealOp(None, Op.pop),
        TealOp(None, Op.byte, '"3"'),
        TealOp(None, Op.retsub),
        TealLabel(None, subroutine2L4Label),
        TealOp(None, Op.pop),
        TealOp(None, Op.byte, '"4"'),
        TealOp(None, Op.retsub),
    ]

    subroutine3Label = LabelReference(subroutineToLabel[subroutine3])
    subroutine3L1Label = LabelReference("l1")
    subroutine3Ops = [
        TealLabel(None, subroutine3L1Label),
        TealOp(None, Op.app_local_put),
        TealOp(None, Op.retsub),
        TealOp(None, Op.b, subroutine3L1Label),
    ]

    l1Label = LabelReference("l1")
    mainOps = [
        TealOp(None, Op.byte, '"account"'),
        TealOp(None, Op.byte, '"key"'),
        TealOp(None, Op.byte, '"value"'),
        TealOp(None, Op.callsub, subroutine3Label),
        TealOp(None, Op.txn, "Fee"),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bz, l1Label),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine2Label),
        TealOp(None, Op.pop),
        TealOp(None, Op.callsub, subroutine1Label),
        TealOp(None, Op.return_),
        TealLabel(None, l1Label),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    expectedL1Label = LabelReference("main_l1")
    expectedSubroutine1Label = LabelReference("sub0")
    expectedSubroutine2Label = LabelReference("sub1")
    expectedSubroutine2L1Label = LabelReference("sub1_l1")
    expectedSubroutine2L2Label = LabelReference("sub1_l2")
    expectedSubroutine2L3Label = LabelReference("sub1_l3")
    expectedSubroutine2L4Label = LabelReference("sub1_l4")
    expectedSubroutine3Label = LabelReference("sub2")
    expectedSubroutine3L1Label = LabelReference("sub2_l1")
    expected = [
        TealOp(None, Op.byte, '"account"'),
        TealOp(None, Op.byte, '"key"'),
        TealOp(None, Op.byte, '"value"'),
        TealOp(None, Op.callsub, subroutine3Label),
        TealOp(None, Op.txn, "Fee"),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.eq),
        TealOp(None, Op.bz, l1Label),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.callsub, subroutine2Label),
        TealOp(None, Op.pop),
        TealOp(None, Op.callsub, subroutine1Label),
        TealOp(None, Op.return_),
        TealLabel(None, l1Label),
        TealOp(None, Op.int, 0),
        TealOp(None, Op.return_),
        TealLabel(None, expectedSubroutine1Label, "sub1Impl"),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.add),
        TealOp(None, Op.add),
        TealOp(None, Op.retsub),
        TealLabel(None, expectedSubroutine2Label, "sub2Impl"),
        TealOp(None, Op.dup),
        TealOp(None, Op.int, 1),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, expectedSubroutine2L1Label),
        TealOp(None, Op.dup),
        TealOp(None, Op.int, 2),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, expectedSubroutine2L2Label),
        TealOp(None, Op.dup),
        TealOp(None, Op.int, 3),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, expectedSubroutine2L3Label),
        TealOp(None, Op.dup),
        TealOp(None, Op.int, 4),
        TealOp(None, Op.eq),
        TealOp(None, Op.bnz, expectedSubroutine2L4Label),
        TealOp(None, Op.err),
        TealLabel(None, expectedSubroutine2L1Label),
        TealOp(None, Op.pop),
        TealOp(None, Op.byte, '"1"'),
        TealOp(None, Op.retsub),
        TealLabel(None, expectedSubroutine2L2Label),
        TealOp(None, Op.pop),
        TealOp(None, Op.byte, '"2"'),
        TealOp(None, Op.retsub),
        TealLabel(None, expectedSubroutine2L3Label),
        TealOp(None, Op.pop),
        TealOp(None, Op.byte, '"3"'),
        TealOp(None, Op.retsub),
        TealLabel(None, expectedSubroutine2L4Label),
        TealOp(None, Op.pop),
        TealOp(None, Op.byte, '"4"'),
        TealOp(None, Op.retsub),
        TealLabel(None, expectedSubroutine3Label, "sub3Impl"),
        TealLabel(None, expectedSubroutine3L1Label),
        TealOp(None, Op.app_local_put),
        TealOp(None, Op.retsub),
        TealOp(None, Op.b, expectedSubroutine3L1Label),
    ]

    actual = flattenSubroutines(subroutineMapping, subroutineToLabel)

    assert actual == expected
