from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_from_op_no_args():
    op = TealOp(None, Op.int, 1)

    expected = TealSimpleBlock([op])

    actual, _ = TealBlock.FromOp(options, op)

    assert actual == expected


def test_from_op_1_arg():
    op = TealOp(None, Op.pop)
    arg_1 = Bytes("message")

    expected = TealSimpleBlock([TealOp(arg_1, Op.byte, '"message"'), op])

    actual, _ = TealBlock.FromOp(options, op, arg_1)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)
    actual.validateTree()

    assert actual == expected


def test_from_op_2_args():
    op = TealOp(None, Op.app_global_put)
    arg_1 = Bytes("key")
    arg_2 = Int(5)

    expected = TealSimpleBlock(
        [TealOp(arg_1, Op.byte, '"key"'), TealOp(arg_2, Op.int, 5), op]
    )

    actual, _ = TealBlock.FromOp(options, op, arg_1, arg_2)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)
    actual.validateTree()

    assert actual == expected


def test_from_op_3_args():
    op = TealOp(None, Op.app_local_put)
    arg_1 = Int(0)
    arg_2 = Bytes("key")
    arg_3 = Int(1)
    arg_4 = Int(2)
    arg_3_plus_4 = arg_3 + arg_4

    expected = TealSimpleBlock(
        [
            TealOp(arg_1, Op.int, 0),
            TealOp(arg_2, Op.byte, '"key"'),
            TealOp(arg_3, Op.int, 1),
            TealOp(arg_4, Op.int, 2),
            TealOp(arg_3_plus_4, Op.add),
            op,
        ]
    )

    actual, _ = TealBlock.FromOp(options, op, arg_1, arg_2, arg_3_plus_4)
    actual.addIncoming()
    actual = TealBlock.NormalizeBlocks(actual)
    actual.validateTree()

    assert actual == expected


def test_iterate_single():
    block = TealSimpleBlock([TealOp(None, Op.int, 1)])

    blocks = list(TealBlock.Iterate(block))

    assert blocks == [block]


def test_iterate_sequence():
    block5 = TealSimpleBlock([TealOp(None, Op.int, 5)])
    block4 = TealSimpleBlock([TealOp(None, Op.int, 4)])
    block4.setNextBlock(block5)
    block3 = TealSimpleBlock([TealOp(None, Op.int, 3)])
    block3.setNextBlock(block4)
    block2 = TealSimpleBlock([TealOp(None, Op.int, 2)])
    block2.setNextBlock(block3)
    block1 = TealSimpleBlock([TealOp(None, Op.int, 1)])
    block1.setNextBlock(block2)

    blocks = list(TealBlock.Iterate(block1))

    assert blocks == [block1, block2, block3, block4, block5]


def test_iterate_branch():
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true"')])
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)

    blocks = list(TealBlock.Iterate(block))

    assert blocks == [block, blockTrue, blockFalse]


def test_iterate_multiple_branch():
    blockTrueTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true true"')])
    blockTrueFalse = TealSimpleBlock([TealOp(None, Op.byte, '"true false"')])
    blockTrueBranch = TealConditionalBlock([])
    blockTrueBranch.setTrueBlock(blockTrueTrue)
    blockTrueBranch.setFalseBlock(blockTrueFalse)
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueBranch)
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)

    blocks = list(TealBlock.Iterate(block))

    assert blocks == [
        block,
        blockTrue,
        blockFalse,
        blockTrueBranch,
        blockTrueTrue,
        blockTrueFalse,
    ]


def test_iterate_branch_converge():
    blockEnd = TealSimpleBlock([TealOp(None, Op.return_)])
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true"')])
    blockTrue.setNextBlock(blockEnd)
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    blockFalse.setNextBlock(blockEnd)
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)

    blocks = list(TealBlock.Iterate(block))

    assert blocks == [block, blockTrue, blockFalse, blockEnd]


def test_normalize_single():
    original = TealSimpleBlock([TealOp(None, Op.int, 1)])

    expected = TealSimpleBlock([TealOp(None, Op.int, 1)])

    original.addIncoming()
    actual = TealBlock.NormalizeBlocks(original)
    actual.validateTree()

    assert actual == expected


def test_normalize_sequence():
    block6 = TealSimpleBlock([])
    block5 = TealSimpleBlock([TealOp(None, Op.int, 5)])
    block5.setNextBlock(block6)
    block4 = TealSimpleBlock([TealOp(None, Op.int, 4)])
    block4.setNextBlock(block5)
    block3 = TealSimpleBlock([TealOp(None, Op.int, 3)])
    block3.setNextBlock(block4)
    block2 = TealSimpleBlock([TealOp(None, Op.int, 2)])
    block2.setNextBlock(block3)
    block1 = TealSimpleBlock([TealOp(None, Op.int, 1)])
    block1.setNextBlock(block2)

    expected = TealSimpleBlock(
        [
            TealOp(None, Op.int, 1),
            TealOp(None, Op.int, 2),
            TealOp(None, Op.int, 3),
            TealOp(None, Op.int, 4),
            TealOp(None, Op.int, 5),
        ]
    )

    block1.addIncoming()
    actual = TealBlock.NormalizeBlocks(block1)
    actual.validateTree()

    assert actual == expected


def test_normalize_branch():
    blockTrueNext = TealSimpleBlock([TealOp(None, Op.int, 4)])
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueNext)
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    blockBranch = TealConditionalBlock([TealOp(None, Op.int, 1)])
    blockBranch.setTrueBlock(blockTrue)
    blockBranch.setFalseBlock(blockFalse)
    original = TealSimpleBlock([])
    original.setNextBlock(blockBranch)

    expectedTrue = TealSimpleBlock(
        [TealOp(None, Op.byte, '"true"'), TealOp(None, Op.int, 4)]
    )
    expectedFalse = TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    expected = TealConditionalBlock([TealOp(None, Op.int, 1)])
    expected.setTrueBlock(expectedTrue)
    expected.setFalseBlock(expectedFalse)

    original.addIncoming()
    actual = TealBlock.NormalizeBlocks(original)
    actual.validateTree()

    assert actual == expected


def test_normalize_branch_converge():
    blockEnd = TealSimpleBlock([])
    blockTrueNext = TealSimpleBlock([TealOp(None, Op.int, 4)])
    blockTrueNext.setNextBlock(blockEnd)
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true"')])
    blockTrue.setNextBlock(blockTrueNext)
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    blockFalse.setNextBlock(blockEnd)
    blockBranch = TealConditionalBlock([TealOp(None, Op.int, 1)])
    blockBranch.setTrueBlock(blockTrue)
    blockBranch.setFalseBlock(blockFalse)
    original = TealSimpleBlock([])
    original.setNextBlock(blockBranch)

    expectedEnd = TealSimpleBlock([])
    expectedTrue = TealSimpleBlock(
        [TealOp(None, Op.byte, '"true"'), TealOp(None, Op.int, 4)]
    )
    expectedTrue.setNextBlock(expectedEnd)
    expectedFalse = TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    expectedFalse.setNextBlock(expectedEnd)
    expected = TealConditionalBlock([TealOp(None, Op.int, 1)])
    expected.setTrueBlock(expectedTrue)
    expected.setFalseBlock(expectedFalse)

    original.addIncoming()
    actual = TealBlock.NormalizeBlocks(original)
    actual.validateTree()

    assert actual == expected
