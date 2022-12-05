# WARNING: this logic sig is for demo purposes only

from pyteal import (
    And,
    Arg,
    Btoi,
    Bytes,
    Expr,
    Global,
    If,
    Int,
    Pop,
    ScratchVar,
    Seq,
    Subroutine,
    TealType,
    Txn,
    TxnType,
)

ONE_ALGO = Int(1_000_000)


@Subroutine(TealType.uint64)
def root_closeness(A, B, C, X):
    left = ScratchVar(TealType.uint64)
    right = ScratchVar(TealType.uint64)
    return Seq(
        left.store(A * X * X + C),
        right.store(B * X),
        If(left.load() < right.load())
        .Then(right.load() - left.load())
        .Else(left.load() - right.load()),
    )


@Subroutine(TealType.uint64)
def calculate_prize(closeness):
    return (
        If(closeness + Int(1) < Int(20))
        .Then(ONE_ALGO * (Int(10) - (closeness + Int(1)) / Int(2)))
        .Else(Int(0))
    )


def logicsig(a: int, p: int, q: int) -> Expr:
    """
    Choices
    * (a, p, q) = (1, 5, 7)
    * compiling on program version 5 and
    * with assembleConstants = True
    results in Logic-Sig Contract Account Address:
    WO3TQD3WBSDKB6WEHUMSEBFH53GZVVXYGPWYDWKUZCKEXTVCDNDHJGG6II
    """
    assert all(
        isinstance(x, int) and p < q and a > 0 and x >= 0 for x in (a, p, q)
    ), f"require non-negative ints a, p, q with p < q but got {a, p, q}"

    b, c = a * (p + q), a * p * q
    msg = Bytes(f"Can you factor {a} * x^2 - {b} * x + {c} ?")

    A, B, C = Int(a), Int(b), Int(c)
    X1 = Btoi(Arg(0))
    X2 = Btoi(Arg(1))
    C1 = ScratchVar(TealType.uint64)
    C2 = ScratchVar(TealType.uint64)
    SUM = ScratchVar(TealType.uint64)
    PRIZE = ScratchVar(TealType.uint64)
    return Seq(
        Pop(msg),
        C1.store(root_closeness(A, B, C, X1)),
        C2.store(root_closeness(A, B, C, X2)),
        SUM.store(C1.load() + C2.load()),
        PRIZE.store(calculate_prize(SUM.load())),
        And(
            Txn.type_enum() == TxnType.Payment,
            Txn.close_remainder_to() == Global.zero_address(),
            X1 != X2,
            PRIZE.load(),
            Txn.amount() == PRIZE.load(),
        ),
    )


def create(a, b, c):
    return logicsig(*map(lambda x: int(x), (a, b, c)))
