import pytest

import pyteal as pt

from .compile_asserts import assert_new_v_old


def user_guide_snippet_dynamic_scratch_var() -> pt.Expr:
    """
    The user guide docs use the test to illustrate `pt.DynamicScratchVar` usage.  pt.If the test breaks, then the user guide docs must be updated along with the test.
    """

    s = pt.ScratchVar(pt.TealType.uint64)
    d = pt.DynamicScratchVar(pt.TealType.uint64)

    return pt.Seq(
        d.set_index(s),
        s.store(pt.Int(7)),
        d.store(d.load() + pt.Int(3)),
        pt.Assert(s.load() == pt.Int(10)),
        pt.Int(1),
    )


def user_guide_snippet_recursiveIsEven():
    @pt.Subroutine(pt.TealType.uint64)
    def recursiveIsEven(i):
        return (
            pt.If(i == pt.Int(0))
            .Then(pt.Int(1))
            .ElseIf(i == pt.Int(1))
            .Then(pt.Int(0))
            .Else(recursiveIsEven(i - pt.Int(2)))
        )

    return recursiveIsEven(pt.Int(15))


def user_guide_snippet_ILLEGAL_recursion():
    @pt.Subroutine(pt.TealType.none)
    def ILLEGAL_recursion(i: pt.ScratchVar):
        return (
            pt.If(i.load() == pt.Int(0))
            .Then(i.store(pt.Int(1)))
            .ElseIf(i.load() == pt.Int(1))
            .Then(i.store(pt.Int(0)))
            .Else(pt.Seq(i.store(i.load() - pt.Int(2)), ILLEGAL_recursion(i)))
        )

    i = pt.ScratchVar(pt.TealType.uint64)
    return pt.Seq(i.store(pt.Int(15)), ILLEGAL_recursion(i), pt.Int(1))


USER_GUIDE_SNIPPETS_COPACETIC = [
    user_guide_snippet_dynamic_scratch_var,
    user_guide_snippet_recursiveIsEven,
]


@pytest.mark.parametrize("snippet", USER_GUIDE_SNIPPETS_COPACETIC)
def test_user_guide_snippets_good(snippet):
    assert_new_v_old(snippet, 6)


USER_GUIDE_SNIPPETS_ERRORING = {
    user_guide_snippet_ILLEGAL_recursion: (
        pt.TealInputError,
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
        pt.compileTeal(snippet(), mode=pt.Mode.Application, version=6)

    assert e in str(tie)
