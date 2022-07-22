from pyteal import Subroutine, Expr, TealType


@Subroutine(TealType.uint64)
def thing(a: Expr, b: Expr) -> Expr:
    return a + b
