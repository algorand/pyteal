from pyteal import *

from .compile_asserts import assert_new_v_old, compile_and_save

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
def factorial_BAD(n: ScratchVar):
    tmp = ScratchVar(TealType.uint64)
    return (
        If(n.load() <= Int(1))
        .Then(n.store(Int(1)))
        .Else(
            Seq(
                tmp.store(n.load() - Int(1)),
                factorial_BAD(tmp),
                n.store(n.load() * tmp.load()),
            )
        )
    )


def fac_by_ref_BAD():
    n = ScratchVar(TealType.uint64)
    return Seq(
        n.store(Int(10)),
        factorial_BAD(n),
        n.load(),
    )


@Subroutine(TealType.none)
def factorial(n: ScratchVar):
    tmp = ScratchVar(TealType.uint64)
    return (
        If(n.load() <= Int(1))
        .Then(n.store(Int(1)))
        .Else(
            Seq(
                tmp.store(n.load()),
                n.store(n.load() - Int(1)),
                factorial(n),
                n.store(n.load() * tmp.load()),
            )
        )
    )


def fac_by_ref():
    n = ScratchVar(TealType.uint64)
    return Seq(
        n.store(Int(10)),
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


@Subroutine(TealType.none)
def plus_one(n: ScratchVar):
    tmp = ScratchVar(TealType.uint64)
    return (
        If(n.load() == Int(0))
        .Then(n.store(Int(1)))
        .Else(
            Seq(
                tmp.store(n.load() - Int(1)),
                plus_one(tmp),
                n.store(tmp.load() + Int(1)),
            )
        )
    )


def increment():
    n = ScratchVar(TealType.uint64)
    return Seq(n.store(Int(4)), plus_one(n), Int(1))


@Subroutine(TealType.none)
def tally(n, result: ScratchVar):
    return (
        If(n == Int(0))
        .Then(result.store(Bytes("")))
        .Else(
            Seq(
                tally(n - Int(1), result),
                result.store(Concat(result.load(), Bytes("1"))),
            )
        )
    )


def tallygo():
    result = ScratchVar(TealType.bytes)
    return Seq(result.store(Bytes("dummy")), tally(Int(4), result), Btoi(result.load()))


NEW_CASES = (
    sub_logcat_dynamic,
    swapper,
    wilt_the_stilt,
    fac_by_ref,
    fac_by_ref_BAD,
    sub_mixed,
)


def test_swapper():
    compile_and_save(swapper, 6)


def test_increment():
    compile_and_save(increment, 6)


def test_tally():
    compile_and_save(tallygo, 6)


def test_fac_by_ref_BAD():
    compile_and_save(fac_by_ref_BAD, 6)


def test_new():
    for pt in NEW_CASES:
        assert_new_v_old(pt, 6)


if __name__ == "__main__":
    # test_swapper()
    # test_new()
    # test_increment()
    test_tally()
