import pytest

import pyteal as pt

avm6Options = pt.CompileOptions(version=6)
avm7Options = pt.CompileOptions(version=7)
avm10Options = pt.CompileOptions(version=10)
avm11Options = pt.CompileOptions(version=11)


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


def test_block_v11_fields():
    arg = pt.Int(0)
    cases = [
        ("proposer", "BlkProposer", pt.TealType.bytes),
        ("fees_collected", "BlkFeesCollected", pt.TealType.uint64),
        ("bonus", "BlkBonus", pt.TealType.uint64),
        ("branch", "BlkBranch", pt.TealType.bytes),
        ("fee_sink", "BlkFeeSink", pt.TealType.bytes),
        ("protocol", "BlkProtocol", pt.TealType.bytes),
        ("txn_counter", "BlkTxnCounter", pt.TealType.uint64),
        ("proposer_payout", "BlkProposerPayout", pt.TealType.uint64),
    ]
    for tc in cases:
        block_method = getattr(pt.Block, tc[0])
        expr = block_method(arg)
        assert expr.type_of() == tc[2]

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(arg, pt.Op.int, 0),
                pt.TealOp(expr, pt.Op.block, tc[1]),
            ]
        )

    actual, _ = expr.__teal__(avm11Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm10Options)
