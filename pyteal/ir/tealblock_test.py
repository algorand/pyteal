from typing import NamedTuple, List

import pyteal as pt

options = pt.CompileOptions()


def test_from_op_no_args():
    op = pt.TealOp(None, pt.Op.int, 1)

    expected = pt.TealSimpleBlock([op])

    actual, _ = pt.TealBlock.FromOp(options, op)

    assert actual == expected


def test_from_op_1_arg():
    op = pt.TealOp(None, pt.Op.pop)
    arg_1 = pt.Bytes("message")

    expected = pt.TealSimpleBlock([pt.TealOp(arg_1, pt.Op.byte, '"message"'), op])

    actual, _ = pt.TealBlock.FromOp(options, op, arg_1)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)
    actual.validateTree()

    assert actual == expected


def test_from_op_2_args():
    op = pt.TealOp(None, pt.Op.app_global_put)
    arg_1 = pt.Bytes("key")
    arg_2 = pt.Int(5)

    expected = pt.TealSimpleBlock(
        [pt.TealOp(arg_1, pt.Op.byte, '"key"'), pt.TealOp(arg_2, pt.Op.int, 5), op]
    )

    actual, _ = pt.TealBlock.FromOp(options, op, arg_1, arg_2)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)
    actual.validateTree()

    assert actual == expected


def test_from_op_3_args():
    op = pt.TealOp(None, pt.Op.app_local_put)
    arg_1 = pt.Int(0)
    arg_2 = pt.Bytes("key")
    arg_3 = pt.Int(1)
    arg_4 = pt.Int(2)
    arg_3_plus_4 = arg_3 + arg_4

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg_1, pt.Op.int, 0),
            pt.TealOp(arg_2, pt.Op.byte, '"key"'),
            pt.TealOp(arg_3, pt.Op.int, 1),
            pt.TealOp(arg_4, pt.Op.int, 2),
            pt.TealOp(arg_3_plus_4, pt.Op.add),
            op,
        ]
    )

    actual, _ = pt.TealBlock.FromOp(options, op, arg_1, arg_2, arg_3_plus_4)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)
    actual.validateTree()

    assert actual == expected


def test_iterate_single():
    block = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 1)])

    blocks = list(pt.TealBlock.Iterate(block))

    assert blocks == [block]


def test_iterate_sequence():
    block5 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 5)])
    block4 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 4)])
    block4.setNextBlock(block5)
    block3 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 3)])
    block3.setNextBlock(block4)
    block2 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 2)])
    block2.setNextBlock(block3)
    block1 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 1)])
    block1.setNextBlock(block2)

    blocks = list(pt.TealBlock.Iterate(block1))

    assert blocks == [block1, block2, block3, block4, block5]


def test_iterate_branch():
    blockTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')])
    blockFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    block = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)

    blocks = list(pt.TealBlock.Iterate(block))

    assert blocks == [block, blockTrue, blockFalse]


def test_iterate_multiple_branch():
    blockTrueTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true true"')])
    blockTrueFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true false"')])
    blockTrueBranch = pt.TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    block = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)

    blocks = list(pt.TealBlock.Iterate(block))

    assert blocks == [
        block,
        blockTrue,
        blockFalse,
        blockTrueBranch,
        blockTrueTrue,
        blockTrueFalse,
    ]


def test_iterate_branch_converge():
    blockEnd = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.return_)])
    blockTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')])
    blockTrue.setNextBlock(blockEnd)
    blockFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    blockFalse.setNextBlock(blockEnd)
    block = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)

    blocks = list(pt.TealBlock.Iterate(block))

    assert blocks == [block, blockTrue, blockFalse, blockEnd]


def test_normalize_single():
    original = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 1)])

    expected = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 1)])

    original.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(original)
    actual.validateTree()

    assert actual == expected


def test_normalize_sequence():
    block6 = pt.TealSimpleBlock([])
    block5 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 5)])
    block5.setNextBlock(block6)
    block4 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 4)])
    block4.setNextBlock(block5)
    block3 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 3)])
    block3.setNextBlock(block4)
    block2 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 2)])
    block2.setNextBlock(block3)
    block1 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 1)])
    block1.setNextBlock(block2)

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(None, pt.Op.int, 1),
            pt.TealOp(None, pt.Op.int, 2),
            pt.TealOp(None, pt.Op.int, 3),
            pt.TealOp(None, pt.Op.int, 4),
            pt.TealOp(None, pt.Op.int, 5),
        ]
    )

    block1.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(block1)
    actual.validateTree()

    assert actual == expected


def test_normalize_branch():
    blockTrueNext = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 4)])
    blockTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueNext)
    blockFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    blockBranch = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    blockBranch.setTrueBlock(blockTrue)
    blockBranch.setFalseBlock(blockFalse)
    original = pt.TealSimpleBlock([])
    original.setNextBlock(blockBranch)

    expectedTrue = pt.TealSimpleBlock(
        [pt.TealOp(None, pt.Op.byte, '"true"'), pt.TealOp(None, pt.Op.int, 4)]
    )
    expectedFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    expected = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    expected.setTrueBlock(expectedTrue)
    expected.setFalseBlock(expectedFalse)

    original.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(original)
    actual.validateTree()

    assert actual == expected


def test_normalize_branch_converge():
    blockEnd = pt.TealSimpleBlock([])
    blockTrueNext = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 4)])
    blockTrueNext.setNextBlock(blockEnd)
    blockTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueNext)
    blockFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    blockFalse.setNextBlock(blockEnd)
    blockBranch = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    blockBranch.setTrueBlock(blockTrue)
    blockBranch.setFalseBlock(blockFalse)
    original = pt.TealSimpleBlock([])
    original.setNextBlock(blockBranch)

    expectedEnd = pt.TealSimpleBlock([])
    expectedTrue = pt.TealSimpleBlock(
        [pt.TealOp(None, pt.Op.byte, '"true"'), pt.TealOp(None, pt.Op.int, 4)]
    )
    expectedTrue.setNextBlock(expectedEnd)
    expectedFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    expectedFalse.setNextBlock(expectedEnd)
    expected = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    expected.setTrueBlock(expectedTrue)
    expected.setFalseBlock(expectedFalse)

    original.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(original)
    actual.validateTree()

    assert actual == expected


def test_GetReferencedScratchSlots():
    a = pt.ScratchSlot()
    b = pt.ScratchSlot()
    c = pt.ScratchSlot()
    d = pt.ScratchSlot()

    end = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.load, d)])
    trueBranch = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.load, b)])
    trueBranch.setNextBlock(end)
    falseBranch = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.load, c)])
    falseBranch.setNextBlock(end)
    splitBranch = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.load, a)])
    splitBranch.setTrueBlock(trueBranch)
    splitBranch.setFalseBlock(falseBranch)

    slotReferences = pt.TealBlock.GetReferencedScratchSlots(splitBranch)
    assert slotReferences == [a, b, c, d]


def test_MatchScratchSlotReferences():
    class MatchSlotReferenceTest(NamedTuple):
        actual: List[pt.ScratchSlot]
        expected: List[pt.ScratchSlot]
        match: bool

    a = pt.ScratchSlot()
    b = pt.ScratchSlot()
    c = pt.ScratchSlot()
    d = pt.ScratchSlot()

    tests: List[MatchSlotReferenceTest] = [
        MatchSlotReferenceTest(
            actual=[],
            expected=[],
            match=True,
        ),
        MatchSlotReferenceTest(
            actual=[a],
            expected=[],
            match=False,
        ),
        MatchSlotReferenceTest(
            actual=[a],
            expected=[a],
            match=True,
        ),
        MatchSlotReferenceTest(
            actual=[a],
            expected=[b],
            match=True,
        ),
        MatchSlotReferenceTest(
            actual=[a, a],
            expected=[a, a],
            match=True,
        ),
        MatchSlotReferenceTest(
            actual=[a, a],
            expected=[b, b],
            match=True,
        ),
        MatchSlotReferenceTest(
            actual=[a, b],
            expected=[a, b],
            match=True,
        ),
        MatchSlotReferenceTest(
            actual=[a, b],
            expected=[b, c],
            match=False,
        ),
        MatchSlotReferenceTest(
            actual=[a, b],
            expected=[c, d],
            match=True,
        ),
        MatchSlotReferenceTest(
            actual=[a, b, b, a, b],
            expected=[c, d, d, c, d],
            match=True,
        ),
        MatchSlotReferenceTest(
            actual=[a, b, b, a, b],
            expected=[a, d, d, a, d],
            match=True,
        ),
        MatchSlotReferenceTest(
            actual=[a, b, b, a, b],
            expected=[c, a, a, c, a],
            match=False,
        ),
        MatchSlotReferenceTest(
            actual=[a, b, b, a, b],
            expected=[c, d, d, c, c],
            match=False,
        ),
    ]

    for i, test in enumerate(tests):
        assert (
            pt.TealBlock.MatchScratchSlotReferences(test.actual, test.expected)
            == test.match
        ), "Test at index {} failed".format(i)
