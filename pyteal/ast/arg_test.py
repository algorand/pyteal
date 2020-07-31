import pytest

from ..errors import TealInputError
from .arg import Arg

def test_arg():
    Arg(0)

    with pytest.raises(TealInputError):
        Arg("k")

    with pytest.raises(TealInputError):
        Arg(-1)

    with pytest.raises(TealInputError):
        Arg(256)
