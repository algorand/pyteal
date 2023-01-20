import pytest

import pyteal as pt

from tests.compile_asserts import assert_new_v_old

# TODO: remove these skips when the following is fixed: https://github.com/algorand/pyteal/issues/199
STABLE_SLOT_GENERATION = False

# ### TESTS FOR NEW PyTEAL THAT USES PASS-BY-REF / DYNAMIC
@pt.Subroutine(pt.TealType.none)
def logcat_dynamic(first: pt.ScratchVar, an_int):
    return pt.Seq(
        first.store(pt.Concat(first.load(), pt.Itob(an_int))),
        pt.Log(first.load()),
    )


def sub_logcat_dynamic():
    first = pt.ScratchVar(pt.TealType.bytes)
    return pt.Seq(
        first.store(pt.Bytes("hello")),
        logcat_dynamic(first, pt.Int(42)),
        pt.Assert(pt.Bytes("hello42") == first.load()),
        pt.Int(1),
    )


def wilt_the_stilt():
    player_score = pt.DynamicScratchVar(pt.TealType.uint64)

    wilt = pt.ScratchVar(pt.TealType.uint64, 129)
    kobe = pt.ScratchVar(pt.TealType.uint64)
    dt = pt.ScratchVar(pt.TealType.uint64, 131)

    return pt.Seq(
        player_score.set_index(wilt),
        player_score.store(pt.Int(100)),
        player_score.set_index(kobe),
        player_score.store(pt.Int(81)),
        player_score.set_index(dt),
        player_score.store(pt.Int(73)),
        pt.Assert(player_score.load() == pt.Int(73)),
        pt.Assert(player_score.index() == pt.Int(131)),
        player_score.set_index(wilt),
        pt.Assert(player_score.load() == pt.Int(100)),
        pt.Assert(player_score.index() == pt.Int(129)),
        pt.Int(100),
    )


@pt.Subroutine(pt.TealType.none)
def swap(x: pt.ScratchVar, y: pt.ScratchVar):
    z = pt.ScratchVar(pt.TealType.anytype)
    return pt.Seq(
        z.store(x.load()),
        x.store(y.load()),
        y.store(z.load()),
    )


@pt.Subroutine(pt.TealType.none)
def cat(x, y):
    return pt.Pop(pt.Concat(x, y))


def swapper():
    a = pt.ScratchVar(pt.TealType.bytes)
    b = pt.ScratchVar(pt.TealType.bytes)
    return pt.Seq(
        a.store(pt.Bytes("hello")),
        b.store(pt.Bytes("goodbye")),
        cat(a.load(), b.load()),
        swap(a, b),
        pt.Assert(a.load() == pt.Bytes("goodbye")),
        pt.Assert(b.load() == pt.Bytes("hello")),
        pt.Int(1000),
    )


@pt.Subroutine(pt.TealType.uint64)
def mixed_annotations(x: pt.Expr, y: pt.Expr, z: pt.ScratchVar) -> pt.Expr:
    return pt.Seq(
        z.store(x),
        pt.Log(pt.Concat(y, pt.Bytes("="), pt.Itob(x))),
        x,
    )


def sub_mixed():
    x = pt.Int(42)
    y = pt.Bytes("x")
    z = pt.ScratchVar(pt.TealType.uint64)
    return mixed_annotations(x, y, z)


def lots_o_vars():
    z = pt.Int(0)
    one = pt.ScratchVar()
    two = pt.ScratchVar()
    three = pt.ScratchVar()
    four = pt.ScratchVar()
    five = pt.Bytes("five")
    six = pt.Bytes("six")
    seven = pt.Bytes("seven")
    eight = pt.Bytes("eight")
    nine = pt.Bytes("nine")
    ten = pt.Bytes("ten")
    eleven = pt.Bytes("eleven")
    twelve = pt.Bytes("twelve")
    int_cursor = pt.DynamicScratchVar(pt.TealType.uint64)
    bytes_cursor = pt.DynamicScratchVar(pt.TealType.bytes)
    thirteen = pt.ScratchVar(pt.TealType.uint64, 13)
    fourteen = pt.ScratchVar(pt.TealType.bytes, 14)
    fifteen = pt.ScratchVar(pt.TealType.uint64)
    sixteen = pt.ScratchVar(pt.TealType.bytes)
    leet = pt.Int(1337)
    ngl = pt.Bytes("NGL: ")
    return (
        pt.If(
            pt.Or(
                pt.App.id() == pt.Int(0), pt.Txn.application_args.length() == pt.Int(0)
            )
        )
        .Then(pt.Int(1))
        .Else(
            pt.Seq(
                one.store(pt.Int(1)),
                two.store(pt.Bytes("two")),
                three.store(pt.Int(3)),
                four.store(pt.Bytes("four")),
                pt.App.localPut(z, five, pt.Int(5)),
                pt.App.localPut(z, six, six),
                pt.App.localPut(z, seven, pt.Int(7)),
                pt.App.localPut(z, eight, eight),
                pt.App.globalPut(nine, pt.Int(9)),
                pt.App.globalPut(ten, ten),
                pt.App.globalPut(eleven, pt.Int(11)),
                pt.App.globalPut(twelve, twelve),
                one.store(one.load() + leet),
                two.store(pt.Concat(ngl, two.load())),
                three.store(three.load() + leet),
                four.store(pt.Concat(ngl, four.load())),
                pt.App.localPut(z, five, leet + pt.App.localGet(z, five)),
                pt.App.localPut(z, six, pt.Concat(ngl, pt.App.localGet(z, six))),
                pt.App.localPut(z, seven, pt.App.localGet(z, seven)),
                pt.App.localPut(z, eight, pt.Concat(ngl, pt.App.localGet(z, eight))),
                pt.App.globalPut(nine, leet + pt.App.globalGet(nine)),
                pt.App.globalPut(ten, pt.Concat(ngl, pt.App.globalGet(ten))),
                pt.App.globalPut(eleven, leet + pt.App.globalGet(eleven)),
                pt.App.globalPut(twelve, pt.Concat(ngl, pt.App.globalGet(twelve))),
                thirteen.store(pt.Btoi(pt.Txn.application_args[0])),
                fourteen.store(pt.Txn.application_args[1]),
                fifteen.store(pt.Btoi(pt.Txn.application_args[2])),
                sixteen.store(pt.Txn.application_args[3]),
                pt.Pop(one.load()),
                pt.Pop(two.load()),
                pt.Pop(three.load()),
                pt.Pop(four.load()),
                pt.Pop(pt.App.localGet(z, five)),
                pt.Pop(pt.App.localGet(z, six)),
                pt.Pop(pt.App.localGet(z, seven)),
                pt.Pop(pt.App.localGet(z, eight)),
                pt.Pop(pt.App.globalGet(nine)),
                pt.Pop(pt.App.globalGet(ten)),
                pt.Pop(pt.App.globalGet(eleven)),
                pt.Pop(pt.App.globalGet(twelve)),
                int_cursor.set_index(thirteen),
                pt.Log(pt.Itob(int_cursor.load())),
                bytes_cursor.set_index(fourteen),
                pt.Log(bytes_cursor.load()),
                int_cursor.set_index(fifteen),
                pt.Log(pt.Itob(int_cursor.load())),
                bytes_cursor.set_index(sixteen),
                pt.Log(bytes_cursor.load()),
                leet,
            )
        )
    )


def empty_scratches():
    cursor = pt.DynamicScratchVar()
    i1 = pt.ScratchVar(pt.TealType.uint64, 0)
    i2 = pt.ScratchVar(pt.TealType.uint64, 2)
    i3 = pt.ScratchVar(pt.TealType.uint64, 4)
    s1 = pt.ScratchVar(pt.TealType.bytes, 1)
    s2 = pt.ScratchVar(pt.TealType.bytes, 3)
    s3 = pt.ScratchVar(pt.TealType.bytes, 5)
    return pt.Seq(
        cursor.set_index(i1),
        cursor.store(pt.Int(0)),
        cursor.set_index(s1),
        cursor.store(pt.Bytes("")),
        cursor.set_index(i2),
        cursor.store(pt.Int(0)),
        cursor.set_index(s2),
        cursor.store(pt.Bytes("")),
        cursor.set_index(i3),
        cursor.store(pt.Int(0)),
        cursor.set_index(s3),
        cursor.store(pt.Bytes("")),
        pt.Int(42),
    )


@pt.Subroutine(pt.TealType.uint64)
def oldfac(n):
    return pt.If(n < pt.Int(2)).Then(pt.Int(1)).Else(n * oldfac(n - pt.Int(1)))


ISSUE_199_CASES = (
    sub_logcat_dynamic,
    swapper,
    wilt_the_stilt,
    sub_mixed,
    lots_o_vars,
    empty_scratches,
)


@pytest.mark.skipif(not STABLE_SLOT_GENERATION, reason="cf. #199")
@pytest.mark.parametrize("pt", ISSUE_199_CASES)
def test_teal_output_is_unchanged(pt):
    assert_new_v_old(pt, 6, "unchanged")


# #### pt.Subroutine Definitions for pass-by-ref guardrails testing #####
@pt.Subroutine(pt.TealType.uint64)
def ok(x):
    # not really ok at runtime... but should be ok at compile time
    return ok(x)


@pt.Subroutine(pt.TealType.uint64)
def ok_byref(x: pt.ScratchVar):
    return pt.Int(42)


@pt.Subroutine(pt.TealType.uint64)
def ok_indirect1(x):
    return ok_indirect2(x)


@pt.Subroutine(pt.TealType.uint64)
def ok_indirect2(x):
    return ok_indirect1(x)


@pt.Subroutine(pt.TealType.uint64)
def not_ok(x: pt.ScratchVar):
    # not ok both at compile and runtime
    return not_ok(x)


@pt.Subroutine(pt.TealType.uint64)
def not_ok_indirect1(x: pt.ScratchVar):
    return not_ok_indirect2(x)


@pt.Subroutine(pt.TealType.uint64)
def not_ok_indirect2(x: pt.ScratchVar):
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

*c - this is the only "pass by-ref" subroutine
Expect the following error path: c-->g-->a-->c
"""


@pt.Subroutine(pt.TealType.uint64)
def a(x):
    tmp = pt.ScratchVar(pt.TealType.uint64)
    return pt.Seq(tmp.store(x), b(x) + c(tmp) + d(x))


@pt.Subroutine(pt.TealType.uint64)
def b(x):
    return a(x) + e(x) * f(x)


@pt.Subroutine(pt.TealType.uint64)
def c(x: pt.ScratchVar):
    return g(pt.Int(42)) - h(x.load())


@pt.Subroutine(pt.TealType.uint64)
def d(x):
    return d(x) + i(pt.Int(11)) * j(x)


@pt.Subroutine(pt.TealType.uint64)
def e(x):
    return pt.Int(42)


@pt.Subroutine(pt.TealType.uint64)
def f(x):
    return pt.Int(42)


@pt.Subroutine(pt.TealType.uint64)
def g(x):
    return a(pt.Int(17))


@pt.Subroutine(pt.TealType.uint64)
def h(x):
    return pt.Int(42)


@pt.Subroutine(pt.TealType.uint64)
def i(x):
    return pt.Int(42)


@pt.Subroutine(pt.TealType.uint64)
def j(x):
    return pt.Int(42)


@pt.Subroutine(pt.TealType.none)
def tally(n, result: pt.ScratchVar):
    return (
        pt.If(n == pt.Int(0))
        .Then(result.store(pt.Bytes("")))
        .Else(
            pt.Seq(
                tally(n - pt.Int(1), result),
                result.store(pt.Concat(result.load(), pt.Bytes("a"))),
            )
        )
    )


@pt.Subroutine(pt.TealType.none)
def factorial_BAD(n: pt.ScratchVar):
    tmp = pt.ScratchVar(pt.TealType.uint64)
    return (
        pt.If(n.load() <= pt.Int(1))
        .Then(n.store(pt.Int(1)))
        .Else(
            pt.Seq(
                tmp.store(n.load() - pt.Int(1)),
                factorial_BAD(tmp),
                n.store(n.load() * tmp.load()),
            )
        )
    )


@pt.Subroutine(pt.TealType.none)
def factorial(n: pt.ScratchVar):
    tmp = pt.ScratchVar(pt.TealType.uint64)
    return (
        pt.If(n.load() <= pt.Int(1))
        .Then(n.store(pt.Int(1)))
        .Else(
            pt.Seq(
                tmp.store(n.load()),
                n.store(n.load() - pt.Int(1)),
                factorial(n),
                n.store(n.load() * tmp.load()),
            )
        )
    )


@pt.Subroutine(pt.TealType.none)
def plus_one(n: pt.ScratchVar):
    tmp = pt.ScratchVar(pt.TealType.uint64)
    return (
        pt.If(n.load() == pt.Int(0))
        .Then(n.store(pt.Int(1)))
        .Else(
            pt.Seq(
                tmp.store(n.load() - pt.Int(1)),
                plus_one(tmp),
                n.store(tmp.load() + pt.Int(1)),
            )
        )
    )


def make_creatable_factory(approval):
    """
    Wrap a pyteal program with code that:
    * approves immediately in the case of app creation (appId == 0)
    * runs the original code otherwise
    """

    def func():
        return (
            pt.If(pt.Txn.application_id() == pt.Int(0)).Then(pt.Int(1)).Else(approval())
        )

    func.__name__ = approval.__name__
    return func


def fac_by_ref():
    n = pt.ScratchVar(pt.TealType.uint64)
    return pt.Seq(
        n.store(pt.Int(10)),
        factorial(n),
        n.load(),
    )


def fac_by_ref_BAD():
    n = pt.ScratchVar(pt.TealType.uint64)
    return pt.Seq(
        n.store(pt.Int(10)),
        factorial_BAD(n),
        n.load(),
    )


# Proved correct via blackbox testing, but BANNING for now
def fac_by_ref_args():
    n = pt.ScratchVar(pt.TealType.uint64)
    return pt.Seq(
        pt.If(
            pt.Or(
                pt.App.id() == pt.Int(0),
                pt.Txn.application_args.length() == pt.Int(0),
            )
        )
        .Then(pt.Int(1))
        .Else(
            pt.Seq(
                n.store(pt.Btoi(pt.Txn.application_args[0])),
                factorial(n),
                n.load(),
            )
        )
    )


def tallygo():
    result = pt.ScratchVar(pt.TealType.bytes)
    # pt.If-Then is a hook for creating + opting in without providing any args
    return (
        pt.If(
            pt.Or(
                pt.App.id() == pt.Int(0), pt.Txn.application_args.length() == pt.Int(0)
            )
        )
        .Then(pt.Int(1))
        .Else(
            pt.Seq(
                result.store(pt.Bytes("dummy")),
                tally(pt.Int(4), result),
                pt.Btoi(result.load()),
            )
        )
    )


TESTABLE_CASES = [(oldfac, [pt.TealType.uint64])]


# ---- Approval PyTEAL Expressions (COPACETIC) ---- #

approval_ok = ok(pt.Int(42))

x_scratchvar = pt.ScratchVar(pt.TealType.uint64)

approval_ok_byref = pt.Seq(x_scratchvar.store(pt.Int(42)), ok_byref(x_scratchvar))

approval_ok_indirect = ok_indirect1(pt.Int(42))

# ---- BANNED Approval PyTEAL Expressions (wrapped in a function) ---- #


@pt.Subroutine(pt.TealType.none)
def subr_string_mult(s: pt.ScratchVar, n):
    tmp = pt.ScratchVar(pt.TealType.bytes)
    return (
        pt.If(n == pt.Int(0))
        .Then(s.store(pt.Bytes("")))
        .Else(
            pt.Seq(
                tmp.store(s.load()),
                subr_string_mult(s, n - pt.Int(1)),
                s.store(pt.Concat(s.load(), tmp.load())),
            )
        )
    )


def string_mult():
    s = pt.ScratchVar(pt.TealType.bytes)
    return pt.Seq(
        s.store(pt.Txn.application_args[0]),
        subr_string_mult(s, pt.Btoi(pt.Txn.application_args[1])),
        pt.Log(s.load()),
        pt.Int(100),
    )


def approval_not_ok():
    return pt.Seq(x_scratchvar.store(pt.Int(42)), not_ok(x_scratchvar))


def approval_not_ok_indirect():
    return pt.Seq(x_scratchvar.store(pt.Int(42)), not_ok_indirect1(x_scratchvar))


def approval_its_complicated():
    return a(pt.Int(42))


def increment():
    n = pt.ScratchVar(pt.TealType.uint64)
    return pt.Seq(n.store(pt.Int(4)), plus_one(n), pt.Int(1))


COPACETIC_APPROVALS = [approval_ok, approval_ok_byref, approval_ok_indirect]


@pytest.mark.parametrize("approval", COPACETIC_APPROVALS)
def test_pass_by_ref_guardrails_COPACETIC(approval):
    assert pt.compileTeal(approval, pt.Mode.Application, version=6)


ILLEGAL_APPROVALS = {
    approval_not_ok: "not_ok()-->not_ok()",
    approval_not_ok_indirect: "not_ok_indirect1()-->not_ok_indirect2()-->not_ok_indirect1()",
    approval_its_complicated: "c()-->g()-->a()-->c()",
    fac_by_ref: "factorial()-->factorial()",
    fac_by_ref_args: "factorial()-->factorial()",
    fac_by_ref_BAD: "factorial_BAD()-->factorial_BAD()",
    increment: "plus_one()-->plus_one()",
    string_mult: "subr_string_mult()-->subr_string_mult()",
    tallygo: "tally()-->tally()",
}


@pytest.mark.parametrize("approval_func, suffix", ILLEGAL_APPROVALS.items())
def test_pass_by_ref_guardrails_BANNED(approval_func, suffix):
    with pytest.raises(pt.TealInputError) as err:
        pt.compileTeal(approval_func(), pt.Mode.Application, version=6)

    prefix = "ScratchVar arguments not allowed in recursive subroutines, but a recursive call-path was detected: "
    assert f"{prefix}{suffix}" in str(err)


def should_it_work() -> pt.Expr:
    xs = [
        pt.ScratchVar(pt.TealType.uint64),
        pt.ScratchVar(pt.TealType.uint64),
    ]

    def store_initial_values():
        return [s.store(pt.Int(i + 1)) for i, s in enumerate(xs)]

    d = pt.DynamicScratchVar(pt.TealType.uint64)

    @pt.Subroutine(pt.TealType.none)
    def retrieve_and_increment(s: pt.ScratchVar):
        return pt.Seq(d.set_index(s), d.store(d.load() + pt.Int(1)))

    def asserts():
        return [pt.Assert(x.load() == pt.Int(i + 2)) for i, x in enumerate(xs)]

    return pt.Seq(
        pt.Seq(store_initial_values()),
        pt.Seq([retrieve_and_increment(x) for x in xs]),
        pt.Seq(asserts()),
        pt.Int(1),
    )


def test_cannot_set_index_with_dynamic():
    with pytest.raises(pt.TealInputError) as tie:
        pt.compileTeal(should_it_work(), pt.Mode.Application, version=6)

    assert (
        "Only allowed to use ScratchVar objects for setting indices, but was given a"
        in str(tie)
    )
