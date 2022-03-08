from pyteal import *

from .compile_asserts import assert_new_v_old, compile_and_save

# Set the following True, if don't want to run pass-by-ref dependent tests
OLD_CODE_ONLY = False

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


if not OLD_CODE_ONLY:
    #### TESTS FOR NEW PyTEAL THAT USES PASS-BY-REF / DYNAMIC
    @Subroutine(TealType.none)
    def logcat_dynamic(first: ScratchVar, an_int):
        return Seq(
            first.store(Concat(first.load(), Itob(an_int))),
            Log(first.load()),
        )

    def sub_logcat_dynamic():
        first = ScratchVar(TealType.bytes)
        return Seq(
            first.store(Bytes("hello")),
            logcat_dynamic(first, Int(42)),
            Assert(Bytes("hello42") == first.load()),
            Int(1),
        )

    def wilt_the_stilt():
        player_score = DynamicScratchVar(TealType.uint64)

        wilt = ScratchVar(TealType.uint64, 129)
        kobe = ScratchVar(TealType.uint64)
        dt = ScratchVar(TealType.uint64, 131)

        return Seq(
            player_score.set_index(wilt),
            player_score.store(Int(100)),
            player_score.set_index(kobe),
            player_score.store(Int(81)),
            player_score.set_index(dt),
            player_score.store(Int(73)),
            Assert(player_score.load() == Int(73)),
            Assert(player_score.index() == Int(131)),
            player_score.set_index(wilt),
            Assert(player_score.load() == Int(100)),
            Assert(player_score.index() == Int(129)),
            Int(100),
        )

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

    @Subroutine(TealType.uint64)
    def mixed_annotations(x: Expr, y: Expr, z: ScratchVar) -> Expr:
        return Seq(
            z.store(x),
            Log(Concat(y, Bytes("="), Itob(x))),
            x,
        )

    def sub_mixed():
        x = Int(42)
        y = Bytes("x")
        z = ScratchVar(TealType.uint64)
        return mixed_annotations(x, y, z)


OLD_CASES = (sub_logcat, sub_slowfib, sub_fastfib, sub_even)


def test_old():
    for pt in OLD_CASES:
        assert_new_v_old(pt)


if __name__ == "__main__":
    test_old()


if not OLD_CODE_ONLY:
    NEW_CASES = (
        sub_logcat_dynamic,
        swapper,
        wilt_the_stilt,
        fac_by_ref,
        sub_mixed,
    )

    def test_swapper():
        compile_and_save(swapper)

    def test_new():
        for pt in NEW_CASES:
            assert_new_v_old(pt)

    if __name__ == "__main__":
        test_swapper()
        test_new()
