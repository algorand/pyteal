import pytest

import pyteal as pt

avm2Options = pt.CompileOptions(version=2)
avm3Options = pt.CompileOptions(version=3)
avm4Options = pt.CompileOptions(version=4)
avm5Options = pt.CompileOptions(version=5)


def test_addw():
    expr = pt.AddW(pt.Int(1), pt.Int(2))

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, pt.Op.int, 1),
            pt.TealOp(expr, pt.Op.int, 2),
            pt.TealOp(expr, pt.Op.addw),
            pt.TealOp(expr.output_slots[1].store(), pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0].store(), pt.Op.store, expr.output_slots[0]),
        ]
    )

    actual, _ = expr.__teal__(avm2Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_addw_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.AddW(pt.Int(2), pt.Txn.receiver())

    with pytest.raises(pt.TealTypeError):
        pt.AddW(pt.Txn.sender(), pt.Int(2))
