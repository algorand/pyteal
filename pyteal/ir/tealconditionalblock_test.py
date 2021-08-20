from .. import *


def test_constructor():
    block1 = TealConditionalBlock([])
    assert block1.ops == []
    assert block1.trueBlock is None
    assert block1.falseBlock is None

    block2 = TealConditionalBlock([TealOp(None, Op.int, 1)])
    assert block2.ops == [TealOp(None, Op.int, 1)]
    assert block2.trueBlock is None
    assert block2.falseBlock is None


def test_true_block():
    block = TealConditionalBlock([])
    block.setTrueBlock(TealSimpleBlock([TealOp(None, Op.substring3)]))
    assert block.trueBlock == TealSimpleBlock([TealOp(None, Op.substring3)])
    assert block.getOutgoing() == [TealSimpleBlock([TealOp(None, Op.substring3)])]


def test_false_block():
    block = TealConditionalBlock([])
    block.setFalseBlock(TealSimpleBlock([TealOp(None, Op.substring3)]))
    assert block.falseBlock == TealSimpleBlock([TealOp(None, Op.substring3)])


def test_outgoing():
    emptyBlock = TealConditionalBlock([])
    assert emptyBlock.getOutgoing() == []

    trueBlock = TealConditionalBlock([])
    trueBlock.setTrueBlock(TealSimpleBlock([TealOp(None, Op.byte, '"true"')]))
    assert trueBlock.getOutgoing() == [
        TealSimpleBlock([TealOp(None, Op.byte, '"true"')])
    ]

    falseBlock = TealConditionalBlock([])
    falseBlock.setFalseBlock(TealSimpleBlock([TealOp(None, Op.byte, '"false"')]))
    assert falseBlock.getOutgoing() == [
        TealSimpleBlock([TealOp(None, Op.byte, '"false"')])
    ]

    bothBlock = TealConditionalBlock([])
    bothBlock.setTrueBlock(TealSimpleBlock([TealOp(None, Op.byte, '"true"')]))
    bothBlock.setFalseBlock(TealSimpleBlock([TealOp(None, Op.byte, '"false"')]))
    assert bothBlock.getOutgoing() == [
        TealSimpleBlock([TealOp(None, Op.byte, '"true"')]),
        TealSimpleBlock([TealOp(None, Op.byte, '"false"')]),
    ]
