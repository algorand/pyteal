import pyteal as pt


def test_constructor():
    block1 = pt.TealSimpleBlock([])
    assert block1.ops == []
    assert block1.nextBlock is None

    block2 = pt.TealSimpleBlock([pt.TealOp(None, pt.Op.int, 1)])
    assert block2.ops == [pt.TealOp(None, pt.Op.int, 1)]
    assert block2.nextBlock is None


def test_next_block():
    block = pt.TealSimpleBlock([])
    block.setNextBlock(pt.TealSimpleBlock([pt.TealOp(None, pt.Op.substring3)]))
    assert block.nextBlock == pt.TealSimpleBlock([pt.TealOp(None, pt.Op.substring3)])


def test_outgoing():
    emptyBlock = pt.TealSimpleBlock([])
    assert emptyBlock.getOutgoing() == []

    block = pt.TealSimpleBlock([])
    block.setNextBlock(pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"nextBlock"')]))
    assert block.getOutgoing() == [
        pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"nextBlock"')])
    ]
