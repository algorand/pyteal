from pyteal import *


@Subroutine(TealType.uint64)
def thing(a: Expr, b: Expr) -> Expr:
    return a + b
