import pytest

import pyteal as pt


POSITIVE_CASES = [
    pt.abi.Uint16(),
    pt.abi.Uint32(),
    pt.abi.StaticArray(pt.abi.BoolTypeSpec(), 12),
]


@pytest.mark.parametrize("case", POSITIVE_CASES)
def test_method_return(case):
    m_ret = pt.abi.MethodReturn(case)
    assert m_ret.type_of() == pt.TealType.none
    assert not m_ret.has_return()
    assert str(m_ret) == f"(MethodReturn {case.type_spec()})"


NEGATIVE_CASES = [
    pt.Int(0),
    pt.Bytes("aaaaaaa"),
    pt.abi.Uint16,
    pt.abi.Uint32,
]


@pytest.mark.parametrize("case", NEGATIVE_CASES)
def test_method_return_error(case):
    with pytest.raises(pt.TealInputError):
        pt.abi.MethodReturn(case)
