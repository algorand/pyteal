import pytest

from . import *
from .. import Int, Bytes
from ...types import TealType
from ...errors import TealInputError


POSITIVE_CASES = [
    Uint16(),
    Uint32(),
    StaticArray(BoolTypeSpec(), 12),
]


@pytest.mark.parametrize("case", POSITIVE_CASES)
def test_method_return(case):
    m_ret = MethodReturn(case)
    assert m_ret.type_of() == TealType.none
    assert not m_ret.has_return()
    assert str(m_ret) == f"(MethodReturn {case.type_spec()})"


NEGATIVE_CASES = [
    Int(0),
    Bytes("aaaaaaa"),
]


@pytest.mark.parametrize("case", NEGATIVE_CASES)
def test_method_return_error(case):
    with pytest.raises(TealInputError):
        MethodReturn(case)
