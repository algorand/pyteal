from typing import List, Tuple

import pytest

from pyteal import *

from .compile_asserts import assert_new_v_old, compile_and_save

# TODO: remove thise skips after the following issue has been fixed https://github.com/algorand/pyteal/issues/199
STABLE_SLOT_GENERATION = False

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
                result.store(Concat(result.load(), Bytes("a"))),
            )
        )
    )


def tallygo():
    result = ScratchVar(TealType.bytes)
    # If-Then is a hook for creating + opting in without providing any args
    return (
        If(Or(App.id() == Int(0), Txn.application_args.length() == Int(0)))
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
        If(Or(App.id() == Int(0), Txn.application_args.length() == Int(0)))
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
    with pytest.raises(TealInputError) as e:
        compile_and_save(increment, 6)
    assert (
        "pass-by-ref recursion disallowed. Currently, a recursive @Subroutine may not accept ScratchVar-typed arguments but a possible recursive call-path was detected: plus_one()-->plus_one()"
        in str(e)
    )


# Testable by black-box:
def fac_by_ref_args():
    n = ScratchVar(TealType.uint64)
    return Seq(
        If(Or(App.id() == Int(0), Txn.application_args.length() == Int(0)))
        .Then(Int(1))
        .Else(
            Seq(
                n.store(Btoi(Txn.application_args[0])),
                factorial(n),
                n.load(),
            )
        )
    )


@Subroutine(TealType.none)
def subr_string_mult(s: ScratchVar, n):
    tmp = ScratchVar(TealType.bytes)
    return (
        If(n == Int(0))
        .Then(s.store(Bytes("")))
        .Else(
            Seq(
                tmp.store(s.load()),
                subr_string_mult(s, n - Int(1)),
                s.store(Concat(s.load(), tmp.load())),
            )
        )
    )


def string_mult():
    s = ScratchVar(TealType.bytes)
    return Seq(
        s.store(Txn.application_args[0]),
        subr_string_mult(s, Btoi(Txn.application_args[1])),
        Log(s.load()),
        Int(100),
    )


def empty_scratches():
    cursor = DynamicScratchVar()
    i1 = ScratchVar(TealType.uint64, 0)
    i2 = ScratchVar(TealType.uint64, 2)
    i3 = ScratchVar(TealType.uint64, 4)
    s1 = ScratchVar(TealType.bytes, 1)
    s2 = ScratchVar(TealType.bytes, 3)
    s3 = ScratchVar(TealType.bytes, 5)
    return Seq(
        cursor.set_index(i1),
        cursor.store(Int(0)),
        cursor.set_index(s1),
        cursor.store(Bytes("")),
        cursor.set_index(i2),
        cursor.store(Int(0)),
        cursor.set_index(s2),
        cursor.store(Bytes("")),
        cursor.set_index(i3),
        cursor.store(Int(0)),
        cursor.set_index(s3),
        cursor.store(Bytes("")),
        Int(42),
    )


def should_it_work() -> Expr:
    xs = [
        ScratchVar(TealType.uint64),
        ScratchVar(TealType.uint64),
    ]

    def store_initial_values():
        return [s.store(Int(i + 1)) for i, s in enumerate(xs)]

    d = DynamicScratchVar(TealType.uint64)

    @Subroutine(TealType.none)
    def retrieve_and_increment(s: ScratchVar):
        return Seq(d.set_index(s), d.store(d.load() + Int(1)))

    def asserts():
        return [Assert(x.load() == Int(i + 2)) for i, x in enumerate(xs)]

    return Seq(
        Seq(store_initial_values()),
        Seq([retrieve_and_increment(x) for x in xs]),
        Seq(asserts()),
        Int(1),
    )


def make_creatable_factory(approval):
    """
    Wrap a pyteal program with code that:
    * approves immediately in the case of app creation (appId == 0)
    * runs the original code otherwise
    """

    def func():
        return If(Txn.application_id() == Int(0)).Then(Int(1)).Else(approval())

    func.__name__ = approval.__name__
    return func


@Subroutine(TealType.uint64)
def oldfac(n):
    return If(n < Int(2)).Then(Int(1)).Else(n * oldfac(n - Int(1)))


def wrap_for_semantic_e2e(subr_with_params: Tuple[Tuple[Expr, List[TealType]]]) -> Expr:
    subr, params = subr_with_params

    def arg(i, p):
        arg = Txn.application_args[i]
        if p == TealType.uint64:
            arg = Btoi(arg)
        return arg

    def approval():
        return subr(*(arg(i, p) for i, p in enumerate(params)))

    setattr(approval, "__name__", f"sem_{subr.name()}")

    return approval


TESTABLE_CASES = [(oldfac, [TealType.uint64])]


@pytest.mark.skipif(not STABLE_SLOT_GENERATION, reason="cf. #199")
@pytest.mark.parametrize("pt", map(wrap_for_semantic_e2e, TESTABLE_CASES))
def test_semantic_unchanged(pt):
    assert_new_v_old(pt, 6)


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
    empty_scratches,
    should_it_work,
)


DEPRECATED_CASES = (string_mult, should_it_work)


@pytest.mark.skipif(not STABLE_SLOT_GENERATION, reason="cf. #199")
@pytest.mark.parametrize("pt", CASES)
def test_teal_output_is_unchanged(pt):
    assert_new_v_old(pt, 6)


@pytest.mark.skipif(not STABLE_SLOT_GENERATION, reason="cf. #199")
@pytest.mark.parametrize("pt", map(make_creatable_factory, DEPRECATED_CASES))
def test_deprecated(pt):
    assert_new_v_old(pt, 6)


def test_pass_by_ref_guardrails():
    ##### Subroutine Definitions #####
    @Subroutine(TealType.uint64)
    def ok(x):
        # not really ok at runtime... but should be ok at compile time
        return ok(x)

    @Subroutine(TealType.uint64)
    def ok_byref(x: ScratchVar):
        return Int(42)

    @Subroutine(TealType.uint64)
    def ok_indirect1(x):
        return ok_indirect2(x)

    @Subroutine(TealType.uint64)
    def ok_indirect2(x):
        return ok_indirect1(x)

    @Subroutine(TealType.uint64)
    def not_ok(x: ScratchVar):
        # not ok both at compile and runtime
        return not_ok(x)

    @Subroutine(TealType.uint64)
    def not_ok_indirect1(x: ScratchVar):
        return not_ok_indirect2(x)

    @Subroutine(TealType.uint64)
    def not_ok_indirect2(x: ScratchVar):
        return not_ok_indirect1(x)

    """
    Complex subroutine graph example:

    a --> b --> a (loop)
            --> e 
            --> f
      --> *c--> g --> a (loop)
            --> h 
      --> d --> d (loop)
            --> i
            --> j

    stack, path:    b|c|d  a
                    b|c    a|d

    *c - this is the only "pass by-ref" subroutine
    I expected the following error path "c-->g-->a-->c"
    (but DFS actually gave the equally invalid path: "c-->g-->a-->d-->j-->i-->c")
    """

    @Subroutine(TealType.uint64)
    def a(x):
        tmp = ScratchVar(TealType.uint64)
        return Seq(tmp.store(x), b(x) + c(tmp) + d(x))

    @Subroutine(TealType.uint64)
    def b(x):
        return a(x) + e(x) * f(x)

    @Subroutine(TealType.uint64)
    def c(x: ScratchVar):
        return g(Int(42)) - h(x.load())

    @Subroutine(TealType.uint64)
    def d(x):
        return d(x) + i(Int(11)) * j(x)

    @Subroutine(TealType.uint64)
    def e(x):
        return Int(42)

    @Subroutine(TealType.uint64)
    def f(x):
        return Int(42)

    @Subroutine(TealType.uint64)
    def g(x):
        return a(Int(17))

    @Subroutine(TealType.uint64)
    def h(x):
        return Int(42)

    @Subroutine(TealType.uint64)
    def i(x):
        return Int(42)

    @Subroutine(TealType.uint64)
    def j(x):
        return Int(42)

    ##### Approval PyTEAL Expressions #####

    approval_ok = ok(Int(42))

    x = ScratchVar(TealType.uint64)

    approval_ok_byref = Seq(x.store(Int(42)), ok_byref(x))

    approval_ok_indirect = ok_indirect1(Int(42))

    approval_not_ok = Seq(x.store(Int(42)), not_ok(x))

    approval_not_ok_indirect = Seq(x.store(Int(42)), not_ok_indirect1(x))

    approval_its_complicated = a(Int(42))

    ##### Assertions #####

    assert compileTeal(approval_ok, Mode.Application, version=6)

    assert compileTeal(approval_ok_byref, Mode.Application, version=6)

    assert compileTeal(approval_ok_indirect, Mode.Application, version=6)

    with pytest.raises(TealInputError) as err:
        compileTeal(approval_not_ok, Mode.Application, version=6)

    assert (
        "pass-by-ref recursion disallowed. Currently, a recursive @Subroutine may not accept ScratchVar-typed arguments but a possible recursive call-path was detected: not_ok()-->not_ok()"
        in str(err)
    )

    with pytest.raises(TealInputError) as err:
        compileTeal(approval_not_ok_indirect, Mode.Application, version=6)

    assert (
        "pass-by-ref recursion disallowed. Currently, a recursive @Subroutine may not accept ScratchVar-typed arguments but a possible recursive call-path was detected: not_ok_indirect1()-->not_ok_indirect2()-->not_ok_indirect1()"
        in str(err)
    )

    with pytest.raises(TealInputError) as err:
        compileTeal(approval_its_complicated, Mode.Application, version=6)

    assert (
        "pass-by-ref recursion disallowed. Currently, a recursive @Subroutine may not accept ScratchVar-typed arguments but a possible recursive call-path was detected: c()-->g()-->a()-->c()"
        in str(err)
    )
