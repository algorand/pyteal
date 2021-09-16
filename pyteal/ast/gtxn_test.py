import pytest

from .. import *


def test_gtxn_invalid():
    with pytest.raises(TealInputError):
        Gtxn[-1].fee()

    with pytest.raises(TealInputError):
        Gtxn[MAX_GROUP_SIZE + 1].sender()

    with pytest.raises(TealTypeError):
        Gtxn[Pop(Int(0))].sender()

    with pytest.raises(TealTypeError):
        Gtxn[Bytes("index")].sender()


# txn_test.py performs additional testing
