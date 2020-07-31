import pytest

from ..errors import TealInputError
from .addr import Addr

def test_addr():
    Addr("NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3THMF")

    with pytest.raises(TealInputError):
        Addr("NJUWK3DJNZTWU2LFNRUW4Z3KNFSWY2LOM5VGSZLMNFXGO2TJMVWGS3TH")

    with pytest.raises(TealInputError):
        Addr("000000000000000000000000000000000000000000000000000000000")

    with pytest.raises(TealInputError):
        Addr(2)
