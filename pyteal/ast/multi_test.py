import pytest

from .. import *

# this is not necessary but mypy complains if it's not included
from .. import CompileOptions

options = CompileOptions()

def __test_single(expr: MultiValue):
    assert expr.output_slots[0] != expr.output_slots[1]

    with TealComponent.Context.ignoreExprEquality():
        assert expr.output_slots[0].load().__teal__(options) == ScratchLoad(
            expr.output_slots[0]
        ).__teal__(options)

    with TealComponent.Context.ignoreExprEquality():
        assert expr.output_slots[1].load().__teal__(options) == ScratchLoad(
            expr.output_slots[1]
        ).__teal__(options)

    assert expr.type_of() == TealType.none

def __test_single_conditional(expr: MultiValue, op, args, iargs):
    __test_single(expr)

    expected_call = TealSimpleBlock([
            TealOp(expr, op, *iargs),
            TealOp(expr.output_slots[0].store(), Op.store, expr.output_slots[0]),
            TealOp(expr.output_slots[1].store(), Op.store, expr.output_slots[1])
        ])

    ifExpr = If(expr.output_slots[0].load()).Then(expr.output_slots[1].load()).Else(Bytes("None"))
    ifBlockStart, _ = ifExpr.__teal__(options)
    
    expected_call.setNextBlock(ifBlockStart)
    
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

def __test_single_assert(expr: MultiValue, op, args, iargs):
    __test_single(expr)

    expected_call = TealSimpleBlock([
            TealOp(expr, op, *iargs),
            TealOp(expr.output_slots[0].store(), Op.store, expr.output_slots[0]),
            TealOp(expr.output_slots[1].store(), Op.store, expr.output_slots[1])
        ])

    assertExpr = Seq(Assert(expr.output_slots[0].load()), expr.output_slots[1].load())
    assertBlockStart, _ = assertExpr.__teal__(options)
    
    expected_call.setNextBlock(assertBlockStart)

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

def __test_single_with_vars(expr: MultiValue, op, args, iargs, var1, var2):
    __test_single(expr)

    expected_call = TealSimpleBlock([
            TealOp(expr, op, *iargs),
            TealOp(expr.output_slots[0].store(), Op.store, expr.output_slots[0]),
            TealOp(expr.output_slots[1].store(), Op.store, expr.output_slots[1])
        ])

    varExpr = Seq(var1.store(expr.output_slots[0].load()), var2.store(expr.output_slots[1].load()))
    varBlockStart, _ = varExpr.__teal__(options)
    
    expected_call.setNextBlock(varBlockStart)

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

def test_multi_value():
    ops = (
        Op.app_global_get_ex,
        Op.app_local_get_ex,
        Op.asset_holding_get,
        Op.asset_params_get,
    )
    types = (
        TealType.uint64, 
        TealType.bytes,
        TealType.anytype
    )
    immedate_argv = (
        [], 
        ["AssetFrozen"]
    )
    argv = (
        [], 
        [Int(0)], 
        [Int(1), Int(2)]
    )

    for op in ops:
        for type in types:
            for iargs in immedate_argv:
                for args in argv:
                    reducer = lambda hasValue, value: If(hasValue).Then(value).Else(Bytes("None"))
                    expr = MultiValue(op, [TealType.uint64, type], immediate_args=iargs, args=args).outputReducer(reducer)
                    __test_single_conditional(expr, op, args, iargs)

                    reducer = lambda hasValue, value: Seq(Assert(hasValue), value)
                    expr = MultiValue(op, [TealType.uint64, type], immediate_args=iargs, args=args).outputReducer(reducer)
                    __test_single_assert(expr, op, args, iargs)

                    hasValueVar = ScratchVar(TealType.uint64)
                    valueVar = ScratchVar(type)
                    reducer = lambda hasValue, value: Seq(hasValueVar.store(hasValue), valueVar.store(value))
                    expr = MultiValue(op, [TealType.uint64, type], immediate_args=iargs, args=args).outputReducer(reducer)
                    __test_single_with_vars(expr, op, args, iargs, hasValueVar, valueVar)

                    
