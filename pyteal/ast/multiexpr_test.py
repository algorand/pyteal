import pytest
from typing import List

import pyteal as pt

options = pt.CompileOptions()


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

    actual, _ = expr.__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected
