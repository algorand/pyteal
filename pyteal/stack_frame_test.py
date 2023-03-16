from unittest.mock import Mock, patch

import pytest

from pyteal.stack_frame import NatalStackFrame, PyTealFrame, StackFrame


@pytest.mark.serial
def test_is_pyteal():
    FrameInfo = Mock()
    FrameInfo.return_value = Mock()

    FrameInfo.return_value.filename = "not_pyteal.py"
    sf = StackFrame(FrameInfo(), None, NatalStackFrame())
    assert not sf._is_pyteal()

    FrameInfo.return_value.filename = "blahblah/pyteal/ir/blah"
    sf = StackFrame(FrameInfo(), None, NatalStackFrame())
    assert sf._is_pyteal()

    FrameInfo.return_value.filename = "blahblah/pyteal/not_really..."
    sf = StackFrame(FrameInfo(), None, NatalStackFrame())
    assert not sf._is_pyteal()


@pytest.mark.serial
def test_file():
    FrameInfo = Mock()
    FrameInfo.return_value = Mock()

    FrameInfo.return_value.filename = "not_pyteal.py"
    ptf = PyTealFrame(FrameInfo(), None, NatalStackFrame(), None)
    assert ptf._file is None
    assert ptf.file() == "not_pyteal.py"
    assert ptf._file == "not_pyteal.py"

    from_root = "/Users/AMAZINGalgodev/github/algorand/beaker/beaker/"
    FrameInfo.return_value.filename = from_root + "client/application_client.py"
    ptf = PyTealFrame(FrameInfo(), None, NatalStackFrame(), None)
    assert ptf._file is None
    ending = (
        "../AMAZINGalgodev/github/algorand/beaker/beaker/client/application_client.py"
    )
    assert ptf.file().endswith(ending)
    assert ptf._file == ptf.file()

    with patch("os.path.relpath", return_value="FOOFOO"):
        FrameInfo.return_value.filename = from_root + "client/application_client.py"
        ptf = PyTealFrame(FrameInfo(), None, NatalStackFrame(), None)
        assert ptf._file is None
        assert ptf.file() == "FOOFOO"
        assert ptf._file == "FOOFOO"


def test_root():
    FrameInfo = Mock()
    FrameInfo.return_value = Mock()
    ptf = PyTealFrame(FrameInfo(), None, NatalStackFrame(), None)

    assert ptf._root is None
    with patch("os.getcwd", return_value="FOOFOO"):
        assert ptf.root() == "FOOFOO"
        assert ptf._root == "FOOFOO"
