import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()


def test_maybe_value():
    ops = (
        Op.app_global_get_ex,
        Op.app_local_get_ex,
        Op.asset_holding_get,
        Op.asset_params_get,
    )
    types = (TealType.uint64, TealType.bytes, TealType.anytype)
    immedate_argv = ([], ["AssetFrozen"])
    argv = ([], [Int(0)], [Int(1), Int(2)])

    for op in ops:
        for type in types:
            for iargs in immedate_argv:
                for args in argv:
                    expr = MaybeValue(op, type, immediate_args=iargs, args=args)

                    assert expr.slotOk != expr.slotValue

                    assert expr.hasValue().type_of() == TealType.uint64
                    with TealComponent.Context.ignoreExprEquality():
                        assert expr.hasValue().__teal__(options) == ScratchLoad(
                            expr.slotOk
                        ).__teal__(options)

                    assert expr.value().type_of() == type
                    with TealComponent.Context.ignoreExprEquality():
                        assert expr.value().__teal__(options) == ScratchLoad(
                            expr.slotValue
                        ).__teal__(options)

                    assert expr.type_of() == TealType.none

                    expected_call = TealSimpleBlock(
                        [
                            TealOp(expr, op, *iargs),
                            TealOp(None, Op.store, expr.slotOk),
                            TealOp(None, Op.store, expr.slotValue),
                        ]
                    )

                    if len(args) == 0:
                        expected = expected_call
                    elif len(args) == 1:
                        expected, after_arg = args[0].__teal__(options)
                        after_arg.setNextBlock(expected_call)
                    elif len(args) == 2:
                        expected, after_arg_1 = args[0].__teal__(options)
                        arg_2, after_arg_2 = args[1].__teal__(options)
                        after_arg_1.setNextBlock(arg_2)
                        after_arg_2.setNextBlock(expected_call)

                    expected.addIncoming()
                    expected = TealBlock.NormalizeBlocks(expected)

                    actual, _ = expr.__teal__(options)
                    actual.addIncoming()
                    actual = TealBlock.NormalizeBlocks(actual)

                    with TealComponent.Context.ignoreExprEquality():
                        assert actual == expected
