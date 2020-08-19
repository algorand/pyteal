import pytest

from .. import *

def test_maybe_value():
    ops = (Op.app_global_get_ex, Op.app_local_get_ex, Op.asset_holding_get, Op.asset_params_get)
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
                    assert expr.hasValue().__teal__() == ScratchLoad(expr.slotOk).__teal__()
                    
                    assert expr.value().type_of() == type
                    assert expr.value().__teal__() == ScratchLoad(expr.slotValue).__teal__()

                    assert expr.type_of() == TealType.none
                    assert expr.__teal__() == sum([arg.__teal__() for arg in args], []) + [
                        TealOp(op, *iargs),
                        TealOp(Op.store, expr.slotOk),
                        TealOp(Op.store, expr.slotValue)
                    ]
