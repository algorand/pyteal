import pytest

import pyteal as pt
from pyteal.types import require_type


def test_require_type():
    require_type(pt.Bytes("str"), pt.TealType.bytes)
    assert True


def test_require_type_invalid():
    with pytest.raises(TypeError):
        pt.App.globalGet(["This is certainly invalid"])
