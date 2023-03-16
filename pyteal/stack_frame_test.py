from copy import deepcopy
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
def test_frame_info_is_pyteal_import_and_is_pyteal_static_and_is_user_gen():
    FrameInfo = Mock()
    FrameInfo.return_value = Mock()

    nsf = NatalStackFrame()
    nsf._frames = []

    def mock_nsf(fi):
        ret_nsf = deepcopy(nsf)
        ret_nsf._frames = [StackFrame(fi, None, ret_nsf)]
        return ret_nsf

    FrameInfo.return_value.code_context = ["something random"]
    assert not StackFrame._frame_info_is_pyteal_import(fi := FrameInfo())
    # assert not mock_nsf(fi).is_pyteal_static()

    FrameInfo.return_value.code_context = ["from pyteal import something"]
    assert StackFrame._frame_info_is_pyteal_import(fi := FrameInfo())
    # assert mock_nsf(fi).is_pyteal_static()

    FrameInfo.return_value.code_context = [
        "from pyteal import something, something_else"
    ]
    assert StackFrame._frame_info_is_pyteal_import(fi := FrameInfo())
    # assert mock_nsf(fi).is_pyteal_static()

    FrameInfo.return_value.code_context = [
        "from pyteal.something import something_else"
    ]
    assert StackFrame._frame_info_is_pyteal_import(fi := FrameInfo())
    # assert mock_nsf(fi).is_pyteal_static()

    FrameInfo.return_value.code_context = ["import pyteal.something"]
    assert StackFrame._frame_info_is_pyteal_import(fi := FrameInfo())
    # assert mock_nsf(fi).is_pyteal_static()

    FrameInfo.return_value.code_context = ["import pyteal as pt"]
    assert StackFrame._frame_info_is_pyteal_import(fi := FrameInfo())
    # assert mock_nsf(fi).is_pyteal_static()

    FrameInfo.return_value.code_context = ["foo = pyteal.Expr()"]
    assert not StackFrame._frame_info_is_pyteal_import(fi := FrameInfo())
    # assert not mock_nsf(fi).is_pyteal_static()

    FrameInfo.return_value.code_context = [
        "from pyteal import (",
        "    something",
        "    something_else",
        ")",
    ]
    assert StackFrame._frame_info_is_pyteal_import(fi := FrameInfo())  # noqa: F841
    # assert mock_nsf(fi).is_pyteal_static()


def test_not_py_crud():
    # testing StackFrame._is_py_crud:
    FrameInfo = Mock()
    FrameInfo.return_value = Mock()

    FrameInfo.return_value.code_context = ["something random"]
    FrameInfo.return_value.filename = "not_pycrud.py"
    assert StackFrame._frame_info_not_py_crud(FrameInfo())

    FrameInfo.return_value.code_context = []
    FrameInfo.return_value.filename = "not_pycrud.py"
    assert StackFrame._frame_info_not_py_crud(FrameInfo())

    FrameInfo.return_value.code_context = ["something random"]
    FrameInfo.return_value.filename = "<pycrud.py>"
    assert StackFrame._frame_info_not_py_crud(FrameInfo())

    FrameInfo.return_value.code_context = []
    FrameInfo.return_value.filename = "<pycrud.py>"
    assert not StackFrame._frame_info_not_py_crud(FrameInfo())

    FrameInfo.return_value.code_context = None
    FrameInfo.return_value.filename = "<pycrud.py>"
    assert not StackFrame._frame_info_not_py_crud(FrameInfo())


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


@pytest.mark.serial
def test_root():
    FrameInfo = Mock()
    FrameInfo.return_value = Mock()
    ptf = PyTealFrame(FrameInfo(), None, NatalStackFrame(), None)

    assert ptf._root is None
    with patch("os.getcwd", return_value="FOOFOO"):
        assert ptf.root() == "FOOFOO"
        assert ptf._root == "FOOFOO"
