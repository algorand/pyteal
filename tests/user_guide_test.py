import re
import pytest

from pyteal import *

from .compile_asserts import assert_new_v_old, compile_and_save


def user_guide_snippet_dynamic_scratch_var() -> Expr:
    """
    The user guide docs use the test to illustrate `DynamicScratchVar` usage.  If the test breaks, then the user guide docs must be updated along with the test.
    """

    s = ScratchVar(TealType.uint64)
    d = DynamicScratchVar(TealType.uint64)

    return Seq(
        d.set_index(s),
        s.store(Int(7)),
        d.store(d.load() + Int(3)),
        Assert(s.load() == Int(10)),
        Int(1),
    )


def user_guide_snippet_recursiveIsEven():
    @Subroutine(TealType.uint64)
    def recursiveIsEven(i):
        return (
            If(i == Int(0))
            .Then(Int(1))
            .ElseIf(i == Int(1))
            .Then(Int(0))
            .Else(recursiveIsEven(i - Int(2)))
        )

    return recursiveIsEven(Int(15))


def user_guide_snippet_ILLEGAL_recursion():
    @Subroutine(TealType.none)
    def ILLEGAL_recursion(i: ScratchVar):
        return (
            If(i.load() == Int(0))
            .Then(i.store(Int(1)))
            .ElseIf(i.load() == Int(1))
            .Then(i.store(Int(0)))
            .Else(Seq(i.store(i.load() - Int(2)), ILLEGAL_recursion(i)))
        )

    i = ScratchVar(TealType.uint64)
    return Seq(i.store(Int(15)), ILLEGAL_recursion(i), Int(1))


USER_GUIDE_SNIPPETS_COPACETIC = [
    user_guide_snippet_dynamic_scratch_var,
    user_guide_snippet_recursiveIsEven,
]


@pytest.mark.parametrize("snippet", USER_GUIDE_SNIPPETS_COPACETIC)
def test_user_guide_snippets_good(snippet):
    assert_new_v_old(snippet, 6)


USER_GUIDE_SNIPPETS_ERRORING = {
    user_guide_snippet_ILLEGAL_recursion: (
        TealInputError,
        "ScratchVar arguments not allowed in recursive subroutines, but a recursive call-path was detected: ILLEGAL_recursion()-->ILLEGAL_recursion()",
    )
}


@pytest.mark.parametrize("snippet_etype_e", USER_GUIDE_SNIPPETS_ERRORING.items())
def test_user_guide_snippets_bad(snippet_etype_e):
    snippet, etype_e = snippet_etype_e
    etype, e = etype_e

    print(
        f"Test case function=[{snippet.__name__}]. Expecting error of type {etype} with message <{e}>"
    )
    with pytest.raises(etype) as tie:
        compileTeal(snippet(), mode=Mode.Application, version=6)

    assert e in str(tie)
