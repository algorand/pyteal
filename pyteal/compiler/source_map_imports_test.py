import pyteal as pt
from tests.integration.graviton_test import exp

goodnum = pt.Int(42)


@pt.Subroutine(pt.TealType.uint64)
def double_exp():
    return pt.Return(exp() ** exp())  # type: ignore


@pt.Subroutine(pt.TealType.bytes)
def cat(x, y):
    return pt.Concat(x, y)
