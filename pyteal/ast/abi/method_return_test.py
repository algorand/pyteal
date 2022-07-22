import pytest

import pyteal as pt
from pyteal import abi


POSITIVE_CASES = [
    abi.Uint16(),
    abi.Uint32(),
    abi.StaticArray(abi.StaticArrayTypeSpec(abi.BoolTypeSpec(), 12)),
]


@pytest.mark.parametrize("case", POSITIVE_CASES)
def test_method_return(case):
    m_ret = abi.MethodReturn(case)
    assert m_ret.type_of() == pt.TealType.none
    assert not m_ret.has_return()
    assert str(m_ret) == f"(MethodReturn {case.type_spec()})"


NEGATIVE_CASES = [
    pt.Int(0),
    pt.Bytes("aaaaaaa"),
    abi.Uint16,
    abi.Uint32,
]


@pytest.mark.parametrize("case", NEGATIVE_CASES)
def test_method_return_error(case):
    with pytest.raises(pt.TealInputError):
        abi.MethodReturn(case)
