from pyteal import *

from compile_asserts import assert_new_v_old, compile_and_save


@Subroutine(TealType.none)
def swap(x: ScratchVar, y: ScratchVar):
    z = ScratchVar(TealType.anytype)
    return Seq(
        z.store(x.load()),
        x.store(y.load()),
        y.store(z.load()),
    )


@Subroutine(TealType.none)
def cat(x, y):
    return Pop(Concat(x, y))


def swapper():
    a = ScratchVar(TealType.bytes)
    b = ScratchVar(TealType.bytes)
    return Seq(
        a.store(Bytes("hello")),
        b.store(Bytes("goodbye")),
        cat(a.load(), b.load()),
        swap(a, b),
        Assert(a.load() == Bytes("goodbye")),
        Assert(b.load() == Bytes("hello")),
        Int(1000),
    )


@Subroutine(TealType.none)
def factorial(n: ScratchVar):
    tmp = ScratchVar(TealType.uint64)
    return (
        If(n.load() <= Int(1))
        .Then(n.store(Int(1)))
        .Else(
            Seq(
                tmp.store(n.load() - Int(1)),
                factorial(tmp),
                n.store(n.load() * tmp.load()),
            )
        )
    )


def fac_by_ref():
    n = ScratchVar(TealType.uint64)
    return Seq(
        n.store(Int(42)),
        factorial(n),
        n.load(),
    )


TEST_CASES = (swapper,)


def test_swapper():
    compile_and_save(swapper)


def test_all():
    for pt in TEST_CASES:
        assert_new_v_old(pt)


if __name__ == "__main__":
    test_swapper()
    test_all()
