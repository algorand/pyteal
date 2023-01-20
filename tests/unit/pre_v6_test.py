import pytest

import pyteal as pt

from tests.compile_asserts import assert_new_v_old

# ---- TESTS FOR PyTEAL THAT PREDATE PASS-BY-REF - assert that changes to compiler don't affect the generated TEAL ---- #


@pt.Subroutine(pt.TealType.bytes)
def logcat(some_bytes, an_int):
    catted = pt.ScratchVar(pt.TealType.bytes)
    return pt.Seq(
        catted.store(pt.Concat(some_bytes, pt.Itob(an_int))),
        pt.Log(catted.load()),
        catted.load(),
    )


def sub_logcat():
    return pt.Seq(
        pt.Assert(logcat(pt.Bytes("hello"), pt.Int(42)) == pt.Bytes("hello42")),
        pt.Int(1),
    )


@pt.Subroutine(pt.TealType.uint64)
def slow_fibonacci(n):
    return (
        pt.If(n <= pt.Int(1))
        .Then(n)
        .Else(slow_fibonacci(n - pt.Int(2)) + slow_fibonacci(n - pt.Int(1)))
    )


def sub_slowfib():
    return slow_fibonacci(pt.Int(3))


@pt.Subroutine(pt.TealType.uint64)
def fast_fibonacci(n):
    i = pt.ScratchVar(pt.TealType.uint64)
    a = pt.ScratchVar(pt.TealType.uint64)
    b = pt.ScratchVar(pt.TealType.uint64)
    return pt.Seq(
        a.store(pt.Int(0)),
        b.store(pt.Int(1)),
        pt.For(i.store(pt.Int(1)), i.load() <= n, i.store(i.load() + pt.Int(1))).Do(
            pt.Seq(
                b.store(a.load() + b.load()),
                a.store(b.load() - a.load()),
            )
        ),
        a.load(),
    )


def sub_fastfib():
    return fast_fibonacci(pt.Int(3))


@pt.Subroutine(pt.TealType.uint64)
def recursiveIsEven(i):
    return (
        pt.If(i == pt.Int(0))
        .Then(pt.Int(1))
        .ElseIf(i == pt.Int(1))
        .Then(pt.Int(0))
        .Else(recursiveIsEven(i - pt.Int(2)))
    )


def sub_even():
    return pt.Seq(
        pt.Pop(recursiveIsEven(pt.Int(1000))),
        recursiveIsEven(pt.Int(1001)),
    )


PT_CASES = (sub_logcat, sub_slowfib, sub_fastfib, sub_even)


@pytest.mark.parametrize("pt_case", PT_CASES)
def test_old(pt_case):
    assert_new_v_old(pt_case, 5, "pre_v6")
