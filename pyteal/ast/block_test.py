import pytest

import pyteal as pt

avm6Options = pt.CompileOptions(version=6)
avm7Options = pt.CompileOptions(version=7)


def test_block_seed():
    arg = pt.Int(0)
    expr = pt.Block.seed(arg)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.block, "BlkSeed"),
        ]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm6Options)


def test_block_seed_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Block.seed(pt.Bytes(""))


def test_block_timestamp():
    arg = pt.Int(0)
    expr = pt.Block.timestamp(arg)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(arg, pt.Op.int, 0),
            pt.TealOp(expr, pt.Op.block, "BlkTimestamp"),
        ]
    )

    actual, _ = expr.__teal__(avm7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm6Options)


def test_block_timestamp_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.Block.timestamp(pt.Txn.sender())
