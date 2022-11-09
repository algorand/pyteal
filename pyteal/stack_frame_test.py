from unittest.mock import Mock

from pyteal.stack_frame import StackFrame

"""
TODO: some unit tests
"""


def test_is_pyteal():
    FrameInfo = Mock()
    FrameInfo.return_value = Mock()

    FrameInfo.return_value.filename = "not_pyteal.py"
    sf = StackFrame(FrameInfo(), None)
    assert not sf._is_pyteal()

    FrameInfo.return_value.filename = "blahblah/pyteal/ir/blah"
    sf = StackFrame(FrameInfo(), None)
    assert sf._is_pyteal()

    FrameInfo.return_value.filename = "blahblah/pyteal/not_really..."
    sf = StackFrame(FrameInfo(), None)
    assert not sf._is_pyteal()
