from .. import *

def test_constructor():
    block1 = TealConditionalBlock([])
    assert block1.ops == []
    assert block1.trueBlock is None
    assert block1.falseBlock is None

    block2 = TealConditionalBlock([TealOp(Op.int, 1)])
    assert block2.ops == [TealOp(Op.int, 1)]
    assert block2.trueBlock is None
    assert block2.falseBlock is None

def test_true_block():
    block = TealConditionalBlock([])
    block.setTrueBlock(TealSimpleBlock([TealOp(Op.substring3)]))
    assert block.trueBlock == TealSimpleBlock([TealOp(Op.substring3)])
    assert block.getOutgoing() == [TealSimpleBlock([TealOp(Op.substring3)])]

def test_false_block():
    block = TealConditionalBlock([])
    block.setFalseBlock(TealSimpleBlock([TealOp(Op.substring3)]))
    assert block.falseBlock == TealSimpleBlock([TealOp(Op.substring3)])

def test_outgoing():
    emptyBlock = TealConditionalBlock([])
    assert emptyBlock.getOutgoing() == []

    trueBlock = TealConditionalBlock([])
    trueBlock.setTrueBlock(TealSimpleBlock([TealOp(Op.byte, "\"true\"")]))
    assert trueBlock.getOutgoing() == [TealSimpleBlock([TealOp(Op.byte, "\"true\"")])]

    falseBlock = TealConditionalBlock([])
    falseBlock.setFalseBlock(TealSimpleBlock([TealOp(Op.byte, "\"false\"")]))
    assert falseBlock.getOutgoing() == [TealSimpleBlock([TealOp(Op.byte, "\"false\"")])]

    bothBlock = TealConditionalBlock([])
    bothBlock.setTrueBlock(TealSimpleBlock([TealOp(Op.byte, "\"true\"")]))
    bothBlock.setFalseBlock(TealSimpleBlock([TealOp(Op.byte, "\"false\"")]))
    assert bothBlock.getOutgoing() == [TealSimpleBlock([TealOp(Op.byte, "\"true\"")]), TealSimpleBlock([TealOp(Op.byte, "\"false\"")])]
