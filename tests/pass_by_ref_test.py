import pytest

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


def fac_by_ref_args():
    n = ScratchVar(TealType.uint64)
    return Seq(
        If(Or(App.id() == Int(0), Txn.num_app_args() == Int(0)))
        .Then(Int(1))
        .Else(
            Seq(
                n.store(Btoi(Txn.application_args[0])),
                factorial(n),
                n.load(),
            )
        )
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
                result.store(Concat(result.load(), Bytes("a"))),
            )
        )
    )


def tallygo():
    result = ScratchVar(TealType.bytes)
    # If-Then is a hook for creating + opting in without providing any args
    return (
        If(Or(App.id() == Int(0), Txn.num_app_args() == Int(0)))
        .Then(Int(1))
        .Else(
            Seq(
                result.store(Bytes("dummy")), tally(Int(4), result), Btoi(result.load())
            )
        )
    )


def lots_o_vars():
    z = Int(0)
    one = ScratchVar()
    two = ScratchVar()
    three = ScratchVar()
    four = ScratchVar()
    five = Bytes("five")
    six = Bytes("six")
    seven = Bytes("seven")
    eight = Bytes("eight")
    nine = Bytes("nine")
    ten = Bytes("ten")
    eleven = Bytes("eleven")
    twelve = Bytes("twelve")
    int_cursor = DynamicScratchVar(TealType.uint64)
    bytes_cursor = DynamicScratchVar(TealType.bytes)
    thirteen = ScratchVar(TealType.uint64, 13)
    fourteen = ScratchVar(TealType.bytes, 14)
    fifteen = ScratchVar(TealType.uint64)
    sixteen = ScratchVar(TealType.bytes)
    leet = Int(1337)
    ngl = Bytes("NGL: ")
    return (
        If(Or(App.id() == Int(0), Txn.num_app_args() == Int(0)))
        .Then(Int(1))
        .Else(
            Seq(
                one.store(Int(1)),
                two.store(Bytes("two")),
                three.store(Int(3)),
                four.store(Bytes("four")),
                App.localPut(z, five, Int(5)),
                App.localPut(z, six, six),
                App.localPut(z, seven, Int(7)),
                App.localPut(z, eight, eight),
                App.globalPut(nine, Int(9)),
                App.globalPut(ten, ten),
                App.globalPut(eleven, Int(11)),
                App.globalPut(twelve, twelve),
                one.store(one.load() + leet),
                two.store(Concat(ngl, two.load())),
                three.store(three.load() + leet),
                four.store(Concat(ngl, four.load())),
                App.localPut(z, five, leet + App.localGet(z, five)),
                App.localPut(z, six, Concat(ngl, App.localGet(z, six))),
                App.localPut(z, seven, App.localGet(z, seven)),
                App.localPut(z, eight, Concat(ngl, App.localGet(z, eight))),
                App.globalPut(nine, leet + App.globalGet(nine)),
                App.globalPut(ten, Concat(ngl, App.globalGet(ten))),
                App.globalPut(eleven, leet + App.globalGet(eleven)),
                App.globalPut(twelve, Concat(ngl, App.globalGet(twelve))),
                thirteen.store(Btoi(Txn.application_args[0])),
                fourteen.store(Txn.application_args[1]),
                fifteen.store(Btoi(Txn.application_args[2])),
                sixteen.store(Txn.application_args[3]),
                Pop(one.load()),
                Pop(two.load()),
                Pop(three.load()),
                Pop(four.load()),
                Pop(App.localGet(z, five)),
                Pop(App.localGet(z, six)),
                Pop(App.localGet(z, seven)),
                Pop(App.localGet(z, eight)),
                Pop(App.globalGet(nine)),
                Pop(App.globalGet(ten)),
                Pop(App.globalGet(eleven)),
                Pop(App.globalGet(twelve)),
                int_cursor.set_index(thirteen),
                Log(Itob(int_cursor.load())),
                bytes_cursor.set_index(fourteen),
                Log(bytes_cursor.load()),
                int_cursor.set_index(fifteen),
                Log(Itob(int_cursor.load())),
                bytes_cursor.set_index(sixteen),
                Log(bytes_cursor.load()),
                leet,
            )
        )
    )


def test_increment():
    compile_and_save(increment, 6)


CASES = (
    sub_logcat_dynamic,
    swapper,
    wilt_the_stilt,
    fac_by_ref,
    fac_by_ref_BAD,
    fac_by_ref_args,
    sub_mixed,
    lots_o_vars,
    tallygo,
)


@pytest.mark.parametrize("pt", CASES)
def test_teal_output_is_unchanged(pt):
    assert_new_v_old(pt, 6)


if __name__ == "__main__":
    test_increment()
    test_teal_output_is_unchanged()
