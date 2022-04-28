import pyteal as pt


def test_constructor():
    block1 = pt.TealConditionalBlock([])
    assert block1.ops == []
    assert block1.trueBlock is None
    assert block1.falseBlock is None

    block2 = pt.TealConditionalBlock([pt.TealOp(None, pt.Op.int, 1)])
    assert block2.ops == [pt.TealOp(None, pt.Op.int, 1)]
    assert block2.trueBlock is None
    assert block2.falseBlock is None


def test_true_block():
    block = pt.TealConditionalBlock([])
    block.setTrueBlock(pt.TealSimpleBlock([pt.TealOp(None, pt.Op.substring3)]))
    assert block.trueBlock == pt.TealSimpleBlock([pt.TealOp(None, pt.Op.substring3)])
    assert block.getOutgoing() == [
        pt.TealSimpleBlock([pt.TealOp(None, pt.Op.substring3)])
    ]


def test_false_block():
    block = pt.TealConditionalBlock([])
    block.setFalseBlock(pt.TealSimpleBlock([pt.TealOp(None, pt.Op.substring3)]))
    assert block.falseBlock == pt.TealSimpleBlock([pt.TealOp(None, pt.Op.substring3)])


def test_outgoing():
    emptyBlock = pt.TealConditionalBlock([])
    assert emptyBlock.getOutgoing() == []

    trueBlock = pt.TealConditionalBlock([])
    trueBlock.setTrueBlock(pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')]))
    assert trueBlock.getOutgoing() == [
        pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')])
    ]

    falseBlock = pt.TealConditionalBlock([])
    falseBlock.setFalseBlock(
        pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    )
    assert falseBlock.getOutgoing() == [
        pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    ]

    bothBlock = pt.TealConditionalBlock([])
    bothBlock.setTrueBlock(pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')]))
    bothBlock.setFalseBlock(
        pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')])
    )
    assert bothBlock.getOutgoing() == [
        pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"true"')]),
        pt.TealSimpleBlock([pt.TealOp(None, pt.Op.byte, '"false"')]),
    ]
