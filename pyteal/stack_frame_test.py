from unittest.mock import Mock, patch

from pyteal.stack_frame import NatalStackFrame, PyTealFrame, StackFrame


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


def test_file():
    FrameInfo = Mock()
    FrameInfo.return_value = Mock()

    FrameInfo.return_value.filename = "not_pyteal.py"
    ptf = PyTealFrame(FrameInfo(), None, NatalStackFrame(), None)
    assert ptf.file() == "not_pyteal.py"

    from_root = "/Users/AMAZINGalgodev/github/algorand/beaker/beaker/"
    FrameInfo.return_value.filename = from_root + "client/application_client.py"
    ptf = PyTealFrame(FrameInfo(), None, NatalStackFrame(), None)
    assert ptf.file().endswith(
        "../AMAZINGalgodev/github/algorand/beaker/beaker/client/application_client.py"
    )

    with patch("os.path.relpath", return_value="FOOFOO"):
        FrameInfo.return_value.filename = from_root + "client/application_client.py"
        ptf = PyTealFrame(FrameInfo(), None, NatalStackFrame(), None)
        assert ptf.file() == "FOOFOO"


def test_root():
    FrameInfo = Mock()
    FrameInfo.return_value = Mock()
    ptf = PyTealFrame(FrameInfo(), None, NatalStackFrame(), None)

    with patch("os.getcwd", return_value="FOOFOO"):
        assert ptf.root() == "FOOFOO"
