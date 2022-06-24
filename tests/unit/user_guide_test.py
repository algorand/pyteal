import pytest

import pyteal as pt
from tests.compile_asserts import assert_new_v_old


def user_guide_snippet_dynamic_scratch_var() -> pt.Expr:
    """
    The user guide docs use the test to illustrate `DynamicScratchVar` usage.  If the test breaks, then the user guide docs must be updated along with the test.
    """
    from pyteal import Assert, Int, DynamicScratchVar, ScratchVar, Seq, TealType

    s = ScratchVar(TealType.uint64)
    d = DynamicScratchVar(TealType.uint64)

    return Seq(
        d.set_index(s),
        s.store(Int(7)),
        d.store(d.load() + Int(3)),
        Assert(s.load() == Int(10)),
        Int(1),
    )


@pytest.mark.parametrize("snippet", [user_guide_snippet_dynamic_scratch_var])
def test_user_guide_snippets(snippet):
    assert_new_v_old(snippet, 6, "user_guide")


def user_guide_snippet_recursiveIsEven():
    from pyteal import If, Int, Subroutine, TealType

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
    from pyteal import If, Int, ScratchVar, Seq, Subroutine, TealType

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


def user_guide_snippet_ABIReturnSubroutine():
    from pyteal import (
        ABIReturnSubroutine,
        Expr,
        For,
        Int,
        ScratchVar,
        Seq,
        Txn,
        TealType,
    )
    from pyteal import abi

    # --- BEGIN doc-comment --- #
    @ABIReturnSubroutine
    def abi_sum(to_sum: abi.DynamicArray[abi.Uint64], *, output: abi.Uint64) -> Expr:
        i = ScratchVar(TealType.uint64)
        value_at_index = abi.Uint64()
        return Seq(
            output.set(0),
            For(
                i.store(Int(0)), i.load() < to_sum.length(), i.store(i.load() + Int(1))
            ).Do(
                Seq(
                    to_sum[i.load()].store_into(value_at_index),
                    output.set(output.get() + value_at_index.get()),
                )
            ),
        )

    program = Seq(
        (to_sum_arr := abi.make(abi.DynamicArray[abi.Uint64])).decode(
            Txn.application_args[1]
        ),
        (res := abi.Uint64()).set(abi_sum(to_sum_arr)),
        pt.abi.MethodReturn(res),
        Int(1),
    )
    # --- END doc-comment --- #
    return program


USER_GUIDE_SNIPPETS_COPACETIC = [
    user_guide_snippet_dynamic_scratch_var,
    user_guide_snippet_recursiveIsEven,
    user_guide_snippet_ABIReturnSubroutine,
]


@pytest.mark.parametrize("snippet", USER_GUIDE_SNIPPETS_COPACETIC)
def test_user_guide_snippets_good(snippet):
    assert_new_v_old(snippet, 6, "user_guide")


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
