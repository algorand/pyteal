from pathlib import Path

from pyteal import *
from pyteal.types import require_type

RETURN_PREFIX = Bytes("base16", "151f7c75")

increment_selector = MethodSignature("increment(uint64)void")
fib1_selector = MethodSignature("fib1(uint64)uint64")
fib2_selector = MethodSignature("fib2(uint64)uint64")
linearTransformation_selector = MethodSignature(
    "linearTransformation(uint64,uint64,uint64,uint64,uint64,uint64)void"
)


@Subroutine(TealType.none)
def increment(x: ScratchVar):
    return Seq(x.store(x.load() + Int(1)))


def approval_increment():
    x = ScratchVar(TealType.uint64, Int(128))

    return Cond(
        [
            Txn.application_args[0] == increment_selector,
            Return(
                Seq(
                    x.store(Int(41)),
                    increment(x),
                    x.load() == Int(42),
                )
            ),
        ],
    )


@Subroutine(TealType.none)
def linearTransformation(a, b, c, d, x: ScratchVar, y: ScratchVar):
    newX = a * x.load() + b * y.load()
    newY = c * x.load() + d * y.load()
    return Seq(
        x.store(newX),
        y.store(newY),
    )


def approval_trans():
    x = ScratchVar(TealType.uint64, Int(127))
    y = ScratchVar(TealType.uint64, Int(128))

    # 90 degrees counter-clockwise:
    a = Int(1)
    b = Int(3)
    c = Int(1)
    d = Int(5)
    return Cond(
        [
            Txn.application_args[0] == linearTransformation_selector,
            Return(
                Seq(
                    x.store(Int(17)),
                    y.store(Int(42)),
                    linearTransformation(a, b, c, d, x, y),
                    Assert(x.load() == Int(143)),
                    Assert(y.load() == Int(227)),
                    linearTransformation(a, b, c, d, x, y),
                    Assert(x.load() == Int(824)),
                    y.load() == Int(1278),
                )
            ),
        ],
    )


@Subroutine(TealType.none)
def addAndPlaceSumInFirstArg(a: ScratchVar, b: Expr):
    return a.store(a.load() + b)


def approval_add100():
    value = ScratchVar(TealType.uint64)
    return Seq(
        value.store(Int(1)),
        addAndPlaceSumInFirstArg(value, Int(100)),
        Log(Itob(value.load())),  # value should now be 101
        Approve(),
    )


@Subroutine(TealType.none)
def fib_swap_step(a: ScratchVar, b: ScratchVar):
    return Seq(
        b.store(b.load() + a.load()),
        a.store(b.load() - a.load()),
    )


@Subroutine(TealType.uint64)
def fib1(n):
    i = ScratchVar(TealType.uint64)
    a = ScratchVar(TealType.uint64)
    b = ScratchVar(TealType.uint64)
    init = Seq(
        i.store(Int(0)),
        a.store(Int(0)),
        b.store(Int(1)),
    )
    cond = i.load() < n - Int(1)
    iter = i.store(i.load() + Int(1))

    return Seq(
        If(n < Int(2))
        .Then(
            Seq(
                uint64_log4return(n),
                Return(n),
            )
        )
        .Else(
            Seq(
                For(init, cond, iter).Do(Seq(fib_swap_step(a, b))),
                uint64_log4return(b.load()),
                Return(b.load()),
            )
        ),
    )


@Subroutine(TealType.uint64)
def fib2(n):
    i = ScratchVar(TealType.uint64)
    a = ScratchVar(TealType.uint64)
    b = ScratchVar(TealType.uint64)

    init = Seq(
        i.store(Int(0)),
        a.store(Int(0)),
        b.store(Int(1)),
    )
    cond = i.load() < n - Int(1)
    iter = i.store(i.load() + Int(1))
    return Seq(
        If(n < Int(2))
        .Then(
            Seq(
                uint64_log4return(n),
                Return(n),
            )
        )
        .Else(
            Seq(
                For(init, cond, iter).Do(
                    Seq(
                        b.store(b.load() + a.load()),
                        a.store(b.load() - a.load()),
                    )
                ),
                uint64_log4return(b.load()),
                Return(b.load()),
            )
        ),
    )


@Subroutine(TealType.none)
def uint64_log4return(value):
    require_type(value, TealType.uint64)
    return Log(Concat(RETURN_PREFIX, Itob(value)))


def approval_fib2():
    x = ScratchVar(TealType.uint64, Int(128))

    return Cond(
        [Txn.application_id() == Int(0), Approve()],
        [
            Txn.on_completion() == OnComplete.DeleteApplication,
            Return(Txn.sender() == Global.creator_address()),
        ],
        [
            Txn.on_completion() == OnComplete.UpdateApplication,
            Return(Txn.sender() == Global.creator_address()),
        ],
        [Txn.on_completion() == OnComplete.CloseOut, Approve()],
        [Txn.on_completion() == OnComplete.OptIn, Approve()],
        [
            Txn.application_args[0] == fib1_selector,
            Return(Seq(Pop(fib1(Txn.application_args[1])), Int(1))),
        ],
        [
            Txn.application_args[0] == fib2_selector,
            Return(Seq(Pop(fib2(Txn.application_args[1])), Int(1))),
        ],
    )


def pyfib1(n: int = 0) -> int:
    if n < 2:
        return n

    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b

    return b


def pyfib2(n: int = 0) -> int:
    if n < 2:
        return n

    a, b = 0, 1
    for _ in range(n - 1):
        b = a + b
        a = b - a

    return b


def clear():
    return Return(Int(1))


if __name__ == "__main__":
    for n in range(43):
        assert pyfib1(n) == pyfib2(n), f"oops {n}: {pyfib1(n)} != {pyfib2(n)}"
        print(f"pyfib({n}) = {pyfib1(n):,}")

    teal = Path.cwd() / "examples" / "application" / "teal"

    # with open(teal / "clear.teal", "w") as f:
    #     f.write(compileTeal(clear(), mode=Mode.Application, version=6))

    with open(teal / "increment.teal", "w") as f:
        f.write(compileTeal(approval_increment(), mode=Mode.Application, version=6))

    with open(teal / "matrix.teal", "w") as f:
        f.write(compileTeal(approval_trans(), mode=Mode.Application, version=6))

    with open(teal / "add100.teal", "w") as f:
        f.write(compileTeal(approval_add100(), mode=Mode.Application, version=6))

    with open(teal / "approval1.teal", "w") as f:
        f.write(compileTeal(approval_fib2(), mode=Mode.Application, version=6))
