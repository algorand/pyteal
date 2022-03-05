from pyteal import *

from .compile_asserts import assert_new_v_old, compile_and_save

#### TESTS FOR PyTEAL THAT PREDATE PASS-BY-REF
@Subroutine(TealType.bytes)
def logcat(some_bytes, an_int):
    catted = ScratchVar(TealType.bytes)
    return Seq(
        catted.store(Concat(some_bytes, Itob(an_int))),
        Log(catted.load()),
        catted.load(),
    )


def sub_logcat():
    return Seq(
        Assert(logcat(Bytes("hello"), Int(42)) == Bytes("hello42")),
        Int(1),
    )


@Subroutine(TealType.uint64)
def slow_fibonacci(n):
    return (
        If(n <= Int(1))
        .Then(n)
        .Else(slow_fibonacci(n - Int(2)) + slow_fibonacci(n - Int(1)))
    )


def sub_slowfib():
    return slow_fibonacci(Int(3))


@Subroutine(TealType.uint64)
def fast_fibonacci(n):
    i = ScratchVar(TealType.uint64)
    a = ScratchVar(TealType.uint64)
    b = ScratchVar(TealType.uint64)
    return Seq(
        a.store(Int(0)),
        b.store(Int(1)),
        For(i.store(Int(1)), i.load() <= n, i.store(i.load() + Int(1))).Do(
            Seq(
                b.store(a.load() + b.load()),
                a.store(b.load() - a.load()),
            )
        ),
        a.load(),
    )


def sub_fastfib():
    return fast_fibonacci(Int(3))


@Subroutine(TealType.uint64)
def recursiveIsEven(i):
    return (
        If(i == Int(0))
        .Then(Int(1))
        .ElseIf(i == Int(1))
        .Then(Int(0))
        .Else(recursiveIsEven(i - Int(2)))
    )


def sub_even():
    return Seq(
        Pop(recursiveIsEven(Int(1000))),
        recursiveIsEven(Int(1001)),
    )


OLD_CASES = (sub_logcat, sub_slowfib, sub_fastfib, sub_even)


def test_old():
    for pt in OLD_CASES:
        assert_new_v_old(pt, 5)


if __name__ == "__main__":
    test_old()
