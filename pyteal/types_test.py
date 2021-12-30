from . import *
from .types import require_type
import pytest


def test_require_type():
    require_type(Bytes("str"), TealType.bytes)
    assert True


def test_require_type_invalid():
    with pytest.raises(TypeError):
        App.globalGet(["This is certainly invalid"])
