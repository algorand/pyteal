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


@pytest.mark.parametrize("snippet", [user_guide_snippet_dynamic_scratch_var])
def test_user_guide_snippets(snippet):
    assert_new_v_old(snippet)
