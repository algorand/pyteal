import pyteal as pt

from pyteal.compiler.sort import sortBlocks


def test_sort_single():
    block = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 1)])
    block.addIncoming()
    block.validateTree()

    expected = [block]
    actual = sortBlocks(block, block)

    assert actual == expected


def test_sort_sequence():
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

    expected = [block1, block2, block3, block4, block5]
    actual = sortBlocks(block1, block5)

    assert actual == expected


def test_sort_branch():
    blockTrue = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')])
    blockFalse = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    block = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    block.setTrueBlock(blockTrue)
    block.setFalseBlock(blockFalse)
    block.addIncoming()
    block.validateTree()

    expected = [block, blockTrue, blockFalse]
    actual = sortBlocks(block, blockFalse)

    assert actual == expected


def test_sort_multiple_branch():
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

    expected = [block, blockFalse, blockTrue, blockEnd]
    actual = sortBlocks(block, blockEnd)

    assert actual == expected
