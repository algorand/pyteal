from collections import OrderedDict

import pyteal as pt

from pyteal.compiler.flatten import flattenBlocks, flattenSubroutines


def test_flattenBlocks_none():
    blocks = []

    expected = []
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_single_empty():
    blocks = [pt.TealSimpleBlock([])]

    expected = []
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_single_one():
    blocks = [pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 1)])]

    expected = [pt.TealOp(None, pt.Op.int, 1)]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_single_many():
    blocks = [
        pt.TealSimpleBlock(
            [
                pt.TealOp(None, pt.Op.int, 1),
                pt.TealOp(None, pt.Op.int, 2),
                pt.TealOp(None, pt.Op.int, 3),
                pt.TealOp(None, pt.Op.add),
                pt.TealOp(None, pt.Op.add),
            ]
        )
    ]

    expected = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.add),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_sequence():
    block5 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 5)])
    block4 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 4)])
    block4.setNextBlock(block5)
    block3 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 3)])
    block3.setNextBlock(block4)
    block2 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 2)])
    block2.setNextBlock(block3)
    block1 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 1)])
    block1.setNextBlock(block2)
    block1.addIncoming()
    block1.validateTree()
    blocks = [block1, block2, block3, block4, block5]

    expected = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.int, 4),
        pt.TealOp(None, pt.Op.int, 5),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_branch():
    blockTrue = pt.TealSimpleBlock(
        [pt.TealOp(None, pt.Op.byte, '"true"'), pt.TealOp(None, pt.Op.return_)]
    )
    blockFalse = pt.TealSimpleBlock(
        [pt.TealOp(None, pt.Op.byte, '"false"'), pt.TealOp(None, pt.Op.return_)]
    )
    block = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [block, blockFalse, blockTrue]

    expected = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.bnz, pt.LabelReference("l2")),
        pt.TealOp(None, pt.Op.byte, '"false"'),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, pt.LabelReference("l2")),
        pt.TealOp(None, pt.Op.byte, '"true"'),
        pt.TealOp(None, pt.Op.return_),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_branch_equal_end_nodes():
    blockTrueEnd = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.return_)])
    blockTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueEnd)
    blockFalseEnd = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.return_)])
    blockFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    blockFalse.setNextBlock(blockFalseEnd)
    block = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [block, blockFalse, blockFalseEnd, blockTrue, blockTrueEnd]

    expected = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.bnz, pt.LabelReference("l3")),
        pt.TealOp(None, pt.Op.byte, '"false"'),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, pt.LabelReference("l3")),
        pt.TealOp(None, pt.Op.byte, '"true"'),
        pt.TealOp(None, pt.Op.return_),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_branch_converge():
    blockEnd = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.return_)])
    blockTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')])
    blockTrue.setNextBlock(blockEnd)
    blockFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    blockFalse.setNextBlock(blockEnd)
    block = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()
    blocks = [block, blockFalse, blockTrue, blockEnd]

    expected = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.bnz, pt.LabelReference("l2")),
        pt.TealOp(None, pt.Op.byte, '"false"'),
        pt.TealOp(None, pt.Op.b, pt.LabelReference("l3")),
        pt.TealLabel(None, pt.LabelReference("l2")),
        pt.TealOp(None, pt.Op.byte, '"true"'),
        pt.TealLabel(None, pt.LabelReference("l3")),
        pt.TealOp(None, pt.Op.return_),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_multiple_branch():
    blockTrueTrue = pt.TealSimpleBlock(
        [pt.TealOp(None, pt.Op.byte, '"true true"'), pt.TealOp(None, pt.Op.return_)]
    )
    blockTrueFalse = pt.TealSimpleBlock(
        [pt.TealOp(None, pt.Op.byte, '"true false"'), pt.TealOp(None, pt.Op.err)]
    )
    blockTrueBranch = pt.TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = pt.TealSimpleBlock(
        [pt.TealOp(None, pt.Op.byte, '"false"'), pt.TealOp(None, pt.Op.return_)]
    )
    block = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
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
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.bnz, pt.LabelReference("l2")),
        pt.TealOp(None, pt.Op.byte, '"false"'),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, pt.LabelReference("l2")),
        pt.TealOp(None, pt.Op.byte, '"true"'),
        pt.TealOp(None, pt.Op.bnz, pt.LabelReference("l5")),
        pt.TealOp(None, pt.Op.byte, '"true false"'),
        pt.TealOp(None, pt.Op.err),
        pt.TealLabel(None, pt.LabelReference("l5")),
        pt.TealOp(None, pt.Op.byte, '"true true"'),
        pt.TealOp(None, pt.Op.return_),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenBlocks_multiple_branch_converge():
    blockEnd = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.return_)])
    blockTrueTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true true"')])
    blockTrueTrue.setNextBlock(blockEnd)
    blockTrueFalse = pt.TealSimpleBlock(
        [pt.TealOp(None, pt.Op.byte, '"true false"'), pt.TealOp(None, pt.Op.err)]
    )
    blockTrueBranch = pt.TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    blockFalse.setNextBlock(blockEnd)
    block = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
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
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.bnz, pt.LabelReference("l2")),
        pt.TealOp(None, pt.Op.byte, '"false"'),
        pt.TealOp(None, pt.Op.b, pt.LabelReference("l6")),
        pt.TealLabel(None, pt.LabelReference("l2")),
        pt.TealOp(None, pt.Op.byte, '"true"'),
        pt.TealOp(None, pt.Op.bnz, pt.LabelReference("l5")),
        pt.TealOp(None, pt.Op.byte, '"true false"'),
        pt.TealOp(None, pt.Op.err),
        pt.TealLabel(None, pt.LabelReference("l5")),
        pt.TealOp(None, pt.Op.byte, '"true true"'),
        pt.TealLabel(None, pt.LabelReference("l6")),
        pt.TealOp(None, pt.Op.return_),
    ]
    actual = flattenBlocks(blocks)

    assert actual == expected


def test_flattenSubroutines_no_subroutines():
    subroutineToLabel = OrderedDict()

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

    expectedL1Label = pt.LabelReference("main_l1")
    expected = [
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, expectedL1Label),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, expectedL1Label),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.return_),
    ]

    opts = pt.CompileOptions()
    actual = flattenSubroutines(subroutineMapping, subroutineToLabel, opts)

    assert actual == expected


def without_expr(comp):
    if isinstance(comp, pt.TealOp):
        return pt.TealOp(None, comp.op, *comp.args)
    if isinstance(comp, pt.TealLabel):
        return pt.TealLabel(None, comp.label, comp.comment)

    assert False, "should never get here"


def test_flattenSubroutines_1_subroutine():
    subroutine = pt.SubroutineDefinition(
        lambda: pt.Int(1) + pt.Int(2) + pt.Int(3), pt.TealType.uint64
    )

    subroutineToLabel = OrderedDict()
    subroutineToLabel[subroutine] = "sub0"

    subroutineLabel = pt.LabelReference(subroutineToLabel[subroutine])
    subroutineOps = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
    ]

    l1Label = pt.LabelReference("l1")
    mainOps = [
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, l1Label),
        pt.TealOp(None, pt.Op.callsub, subroutineLabel),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, l1Label),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.return_),
    ]

    subroutineMapping = {None: mainOps, subroutine: subroutineOps}

    expectedL1Label = pt.LabelReference("main_l1")
    expectedSubroutineLabel = pt.LabelReference("sub0")
    expected = [
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, expectedL1Label),
        pt.TealOp(None, pt.Op.callsub, expectedSubroutineLabel),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, expectedL1Label),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, expectedSubroutineLabel, "<lambda>"),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
    ]

    opts = pt.CompileOptions()
    actual = flattenSubroutines(subroutineMapping, subroutineToLabel, opts)

    assert list(map(without_expr, actual)) == expected


def test_flattenSubroutines_multiple_subroutines():
    def sub1Impl():
        return None

    def sub2Impl(a1):
        return None

    def sub3Impl(a1, a2, a3):
        return None

    subroutine1 = pt.SubroutineDefinition(sub1Impl, pt.TealType.uint64)
    subroutine2 = pt.SubroutineDefinition(sub2Impl, pt.TealType.bytes)
    subroutine3 = pt.SubroutineDefinition(sub3Impl, pt.TealType.none)

    subroutineToLabel = OrderedDict()
    subroutineToLabel[subroutine1] = "sub0"
    subroutineToLabel[subroutine2] = "sub1"
    subroutineToLabel[subroutine3] = "sub2"

    subroutine1Label = pt.LabelReference(subroutineToLabel[subroutine1])
    subroutine1Ops = [
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine2Label = pt.LabelReference(subroutineToLabel[subroutine2])
    subroutine2L1Label = pt.LabelReference("l1")
    subroutine2L2Label = pt.LabelReference("l2")
    subroutine2L3Label = pt.LabelReference("l3")
    subroutine2L4Label = pt.LabelReference("l4")
    subroutine2Ops = [
        pt.TealOp(None, pt.Op.dup),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine2L1Label),
        pt.TealOp(None, pt.Op.dup),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine2L2Label),
        pt.TealOp(None, pt.Op.dup),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine2L3Label),
        pt.TealOp(None, pt.Op.dup),
        pt.TealOp(None, pt.Op.int, 4),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, subroutine2L4Label),
        pt.TealOp(None, pt.Op.err),
        pt.TealLabel(None, subroutine2L1Label),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.byte, '"1"'),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutine2L2Label),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.byte, '"2"'),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutine2L3Label),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.byte, '"3"'),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, subroutine2L4Label),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.byte, '"4"'),
        pt.TealOp(None, pt.Op.retsub),
    ]

    subroutine3Label = pt.LabelReference(subroutineToLabel[subroutine3])
    subroutine3L1Label = pt.LabelReference("l1")
    subroutine3Ops = [
        pt.TealLabel(None, subroutine3L1Label),
        pt.TealOp(None, pt.Op.app_local_put),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealOp(None, pt.Op.b, subroutine3L1Label),
    ]

    l1Label = pt.LabelReference("l1")
    mainOps = [
        pt.TealOp(None, pt.Op.byte, '"account"'),
        pt.TealOp(None, pt.Op.byte, '"key"'),
        pt.TealOp(None, pt.Op.byte, '"value"'),
        pt.TealOp(None, pt.Op.callsub, subroutine3Label),
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, l1Label),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine2Label),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.callsub, subroutine1Label),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, l1Label),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.return_),
    ]

    subroutineMapping = {
        None: mainOps,
        subroutine1: subroutine1Ops,
        subroutine2: subroutine2Ops,
        subroutine3: subroutine3Ops,
    }

    expectedL1Label = pt.LabelReference("main_l1")
    expectedSubroutine1Label = pt.LabelReference("sub0")
    expectedSubroutine2Label = pt.LabelReference("sub1")
    expectedSubroutine2L1Label = pt.LabelReference("sub1_l1")
    expectedSubroutine2L2Label = pt.LabelReference("sub1_l2")
    expectedSubroutine2L3Label = pt.LabelReference("sub1_l3")
    expectedSubroutine2L4Label = pt.LabelReference("sub1_l4")
    expectedSubroutine3Label = pt.LabelReference("sub2")
    expectedSubroutine3L1Label = pt.LabelReference("sub2_l1")
    expected = [
        pt.TealOp(None, pt.Op.byte, '"account"'),
        pt.TealOp(None, pt.Op.byte, '"key"'),
        pt.TealOp(None, pt.Op.byte, '"value"'),
        pt.TealOp(None, pt.Op.callsub, subroutine3Label),
        pt.TealOp(None, pt.Op.txn, "Fee"),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bz, expectedL1Label),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.callsub, subroutine2Label),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.callsub, subroutine1Label),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, expectedL1Label),
        pt.TealOp(None, pt.Op.int, 0),
        pt.TealOp(None, pt.Op.return_),
        pt.TealLabel(None, expectedSubroutine1Label, "sub1Impl"),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.add),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, expectedSubroutine2Label, "sub2Impl"),
        pt.TealOp(None, pt.Op.dup),
        pt.TealOp(None, pt.Op.int, 1),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, expectedSubroutine2L1Label),
        pt.TealOp(None, pt.Op.dup),
        pt.TealOp(None, pt.Op.int, 2),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, expectedSubroutine2L2Label),
        pt.TealOp(None, pt.Op.dup),
        pt.TealOp(None, pt.Op.int, 3),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, expectedSubroutine2L3Label),
        pt.TealOp(None, pt.Op.dup),
        pt.TealOp(None, pt.Op.int, 4),
        pt.TealOp(None, pt.Op.eq),
        pt.TealOp(None, pt.Op.bnz, expectedSubroutine2L4Label),
        pt.TealOp(None, pt.Op.err),
        pt.TealLabel(None, expectedSubroutine2L1Label),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.byte, '"1"'),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, expectedSubroutine2L2Label),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.byte, '"2"'),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, expectedSubroutine2L3Label),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.byte, '"3"'),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, expectedSubroutine2L4Label),
        pt.TealOp(None, pt.Op.pop),
        pt.TealOp(None, pt.Op.byte, '"4"'),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealLabel(None, expectedSubroutine3Label, "sub3Impl"),
        pt.TealLabel(None, expectedSubroutine3L1Label),
        pt.TealOp(None, pt.Op.app_local_put),
        pt.TealOp(None, pt.Op.retsub),
        pt.TealOp(None, pt.Op.b, expectedSubroutine3L1Label),
    ]

    opts = pt.CompileOptions()
    actual = flattenSubroutines(subroutineMapping, subroutineToLabel, opts)

    assert actual == expected
