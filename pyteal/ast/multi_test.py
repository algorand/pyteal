from typing import List

import pyteal as pt

options = pt.CompileOptions()


def __test_single(expr: pt.MultiValue):
    assert expr.output_slots[0] != expr.output_slots[1]

    with pt.TealComponent.Context.ignoreExprEquality():
        assert expr.output_slots[0].load().__teal__(options) == pt.ScratchLoad(
            expr.output_slots[0]
        ).__teal__(options)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert expr.output_slots[1].load().__teal__(options) == pt.ScratchLoad(
            expr.output_slots[1]
        ).__teal__(options)

    assert expr.type_of() == pt.TealType.none


def __test_single_conditional(
    expr: pt.MultiValue, op, args: List[pt.Expr], iargs, reducer
):
    __test_single(expr)

    expected_call = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, op, *iargs),
            pt.TealOp(expr.output_slots[1].store(), pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0].store(), pt.Op.store, expr.output_slots[0]),
        ]
    )

    ifExpr = (
        pt.If(expr.output_slots[1].load())
        .Then(expr.output_slots[0].load())
        .Else(pt.Bytes("None"))
    )
    ifBlockStart, _ = ifExpr.__teal__(options)

    expected_call.setNextBlock(ifBlockStart)

    if len(args) == 0:
        expected: pt.TealBlock = expected_call
    elif len(args) == 1:
        expected, after_arg = args[0].__teal__(options)
        after_arg.setNextBlock(expected_call)
    elif len(args) == 2:
        expected, after_arg_1 = args[0].__teal__(options)
        arg_2, after_arg_2 = args[1].__teal__(options)
        after_arg_1.setNextBlock(arg_2)
        after_arg_2.setNextBlock(expected_call)

    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.outputReducer(reducer).__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def __test_single_assert(expr: pt.MultiValue, op, args: List[pt.Expr], iargs, reducer):
    __test_single(expr)

    expected_call = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, op, *iargs),
            pt.TealOp(expr.output_slots[1].store(), pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0].store(), pt.Op.store, expr.output_slots[0]),
        ]
    )

    assertExpr = pt.Seq(
        pt.Assert(expr.output_slots[1].load()), expr.output_slots[0].load()
    )
    assertBlockStart, _ = assertExpr.__teal__(options)

    expected_call.setNextBlock(assertBlockStart)

    if len(args) == 0:
        expected: pt.TealBlock = expected_call
    elif len(args) == 1:
        expected, after_arg = args[0].__teal__(options)
        after_arg.setNextBlock(expected_call)
    elif len(args) == 2:
        expected, after_arg_1 = args[0].__teal__(options)
        arg_2, after_arg_2 = args[1].__teal__(options)
        after_arg_1.setNextBlock(arg_2)
        after_arg_2.setNextBlock(expected_call)

    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.outputReducer(reducer).__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def __test_single_with_vars(
    expr: pt.MultiValue, op, args: List[pt.Expr], iargs, var1, var2, reducer
):
    __test_single(expr)

    expected_call = pt.TealSimpleBlock(
        [
            pt.TealOp(expr, op, *iargs),
            pt.TealOp(expr.output_slots[1].store(), pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0].store(), pt.Op.store, expr.output_slots[0]),
        ]
    )

    varExpr = pt.Seq(
        var1.store(expr.output_slots[1].load()), var2.store(expr.output_slots[0].load())
    )
    varBlockStart, _ = varExpr.__teal__(options)

    expected_call.setNextBlock(varBlockStart)

    if len(args) == 0:
        expected: pt.TealBlock = expected_call
    elif len(args) == 1:
        expected, after_arg = args[0].__teal__(options)
        after_arg.setNextBlock(expected_call)
    elif len(args) == 2:
        expected, after_arg_1 = args[0].__teal__(options)
        arg_2, after_arg_2 = args[1].__teal__(options)
        after_arg_1.setNextBlock(arg_2)
        after_arg_2.setNextBlock(expected_call)

    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.outputReducer(reducer).__teal__(options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected


def test_multi_value():
    ops = (
        pt.Op.app_global_get_ex,
        pt.Op.app_local_get_ex,
        pt.Op.asset_holding_get,
        pt.Op.asset_params_get,
    )
    types = (pt.TealType.uint64, pt.TealType.bytes, pt.TealType.anytype)
    immedate_argv = ([], ["AssetFrozen"])
    argv = ([], [pt.Int(0)], [pt.Int(1), pt.Int(2)])

    for op in ops:
        for type in types:
            for iargs in immedate_argv:
                for args in argv:
                    reducer = (
                        lambda value, hasValue: pt.If(hasValue)
                        .Then(value)
                        .Else(pt.Bytes("None"))
                    )
                    expr = pt.MultiValue(
                        op, [type, pt.TealType.uint64], immediate_args=iargs, args=args
                    )
                    __test_single_conditional(expr, op, args, iargs, reducer)

                    reducer = lambda value, hasValue: pt.Seq(  # noqa: E731
                        pt.Assert(hasValue), value
                    )
                    expr = pt.MultiValue(
                        op, [type, pt.TealType.uint64], immediate_args=iargs, args=args
                    )
                    __test_single_assert(expr, op, args, iargs, reducer)

                    hasValueVar = pt.ScratchVar(pt.TealType.uint64)
                    valueVar = pt.ScratchVar(type)
                    reducer = lambda value, hasValue: pt.Seq(  # noqa: E731
                        hasValueVar.store(hasValue), valueVar.store(value)
                    )
                    expr = pt.MultiValue(
                        op, [type, pt.TealType.uint64], immediate_args=iargs, args=args
                    )
                    __test_single_with_vars(
                        expr, op, args, iargs, hasValueVar, valueVar, reducer
                    )
