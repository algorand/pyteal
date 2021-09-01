from .. import *

from .sort import sortBlocks


def test_sort_single():
    block = TealSimpleBlock([TealOp(None, Op.int, 1)])
    block.addIncoming()
    block.validateTree()

    expected = [block]
    actual = sortBlocks(block, block)

    assert actual == expected


def test_sort_sequence():
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

    expected = [block1, block2, block3, block4, block5]
    actual = sortBlocks(block1, block5)

    assert actual == expected


def test_sort_branch():
    blockTrue = TealSimpleBlock([TealOp(None, Op.byte, '"true"')])
    blockFalse = TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    block = TealConditionalBlock([TealOp(None, Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()

    expected = [block, blockTrue, blockFalse]
    actual = sortBlocks(block, blockFalse)

    assert actual == expected


def test_sort_multiple_branch():
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
    block.addIncoming()
    block.validateTree()

    expected = [
        block,
        blockTrue,
        blockTrueBranch,
        blockTrueFalse,
        blockTrueTrue,
        blockFalse,
    ]
    actual = sortBlocks(block, blockFalse)

    assert actual == expected


def test_sort_branch_converge():
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

    expected = [block, blockFalse, blockTrue, blockEnd]
    actual = sortBlocks(block, blockEnd)

    assert actual == expected
