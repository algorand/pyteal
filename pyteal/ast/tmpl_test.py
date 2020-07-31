import pytest

from ..errors import TealInputError
from .tmpl import Tmpl

def test_tmpl():
    Tmpl.Int("TMPL_AMNT")
    Tmpl.Bytes("TMPL_NOTE")
    Tmpl.Addr("TMPL_RECEIVER0")

    with pytest.raises(TealInputError):
        Tmpl.Int("whatever")
    
    with pytest.raises(TealInputError):
        Tmpl.Bytes("whatever")
    
    with pytest.raises(TealInputError):
        Tmpl.Addr("whatever")
