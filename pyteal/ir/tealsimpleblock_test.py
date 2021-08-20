from .. import *


def test_constructor():
    block1 = TealSimpleBlock([])
    assert block1.ops == []
    assert block1.nextBlock is None

    block2 = TealSimpleBlock([TealOp(None, Op.int, 1)])
    assert block2.ops == [TealOp(None, Op.int, 1)]
    assert block2.nextBlock is None


def test_next_block():
    block = TealSimpleBlock([])
    block.setNextBlock(TealSimpleBlock([TealOp(None, Op.substring3)]))
    assert block.nextBlock == TealSimpleBlock([TealOp(None, Op.substring3)])


def test_outgoing():
    emptyBlock = TealSimpleBlock([])
    assert emptyBlock.getOutgoing() == []

    block = TealSimpleBlock([])
    block.setNextBlock(TealSimpleBlock([TealOp(None, Op.byte, '"nextBlock"')]))
    assert block.getOutgoing() == [
        TealSimpleBlock([TealOp(None, Op.byte, '"nextBlock"')])
    ]
