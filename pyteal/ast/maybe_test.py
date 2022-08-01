import pyteal as pt

options = pt.CompileOptions()


def assert_MaybeValue_equality(
    actual: pt.MaybeValue, expected: pt.MaybeValue, options: pt.CompileOptions
):
    actual_block, _ = actual.__teal__(options)
    actual_block.addIncoming()
    actual_block = pt.TealBlock.NormalizeBlocks(actual_block)

    expected_block, _ = expected.__teal__(options)
    expected_block.addIncoming()
    expected_block = pt.TealBlock.NormalizeBlocks(expected_block)

    with pt.TealComponent.Context.ignoreExprEquality(), pt.TealComponent.Context.ignoreScratchSlotEquality():
        assert actual_block == expected_block

    assert pt.TealBlock.MatchScratchSlotReferences(
        pt.TealBlock.GetReferencedScratchSlots(actual_block),
        pt.TealBlock.GetReferencedScratchSlots(expected_block),
    )


def test_maybe_value():
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
                    expr = pt.MaybeValue(op, type, immediate_args=iargs, args=args)

                    assert expr.slotOk != expr.slotValue
                    assert expr.output_slots == [expr.slotValue, expr.slotOk]

                    assert expr.hasValue().type_of() == pt.TealType.uint64
                    with pt.TealComponent.Context.ignoreExprEquality():
                        assert expr.hasValue().__teal__(options) == pt.ScratchLoad(
                            expr.slotOk
                        ).__teal__(options)

                    assert expr.value().type_of() == type
                    with pt.TealComponent.Context.ignoreExprEquality():
                        assert expr.value().__teal__(options) == pt.ScratchLoad(
                            expr.slotValue
                        ).__teal__(options)

                    assert expr.type_of() == pt.TealType.none

                    expected_call = pt.TealSimpleBlock(
                        [
                            pt.TealOp(expr, op, *iargs),
                            pt.TealOp(None, pt.Op.store, expr.slotOk),
                            pt.TealOp(None, pt.Op.store, expr.slotValue),
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
                    expected = pt.TealBlock.NormalizeBlocks(expected)

                    actual, _ = expr.__teal__(options)
                    actual.addIncoming()
                    actual = pt.TealBlock.NormalizeBlocks(actual)

                    with pt.TealComponent.Context.ignoreExprEquality():
                        assert actual == expected
