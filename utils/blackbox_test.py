from itertools import product
from pathlib import Path
import pytest

import pyteal as pt

from utils.blackbox import blackbox_pyteal

from tests.compile_asserts import assert_teal_as_expected

TEAL_PATH = Path.cwd() / "utils" / "test" / "teal"


@pt.Subroutine(pt.TealType.none, input_types=[])
def utest_noop():
    return pt.Pop(pt.Int(0))


@pt.Subroutine(
    pt.TealType.none,
    input_types=[pt.TealType.uint64, pt.TealType.bytes, pt.TealType.anytype],
)
def utest_noop_args(x, y, z):
    return pt.Pop(pt.Int(0))


@pt.Subroutine(pt.TealType.uint64, input_types=[])
def utest_int():
    return pt.Int(0)


@pt.Subroutine(
    pt.TealType.uint64,
    input_types=[pt.TealType.uint64, pt.TealType.bytes, pt.TealType.anytype],
)
def utest_int_args(x, y, z):
    return pt.Int(0)


@pt.Subroutine(pt.TealType.bytes, input_types=[])
def utest_bytes():
    return pt.Bytes("")


@pt.Subroutine(
    pt.TealType.bytes,
    input_types=[pt.TealType.uint64, pt.TealType.bytes, pt.TealType.anytype],
)
def utest_bytes_args(x, y, z):
    return pt.Bytes("")


@pt.Subroutine(pt.TealType.anytype, input_types=[])
def utest_any():
    x = pt.ScratchVar(pt.TealType.anytype)
    return pt.Seq(x.store(pt.Int(0)), x.load())


@pt.Subroutine(
    pt.TealType.anytype,
    input_types=[pt.TealType.uint64, pt.TealType.bytes, pt.TealType.anytype],
)
def utest_any_args(x, y, z):
    x = pt.ScratchVar(pt.TealType.anytype)
    return pt.Seq(x.store(pt.Int(0)), x.load())


UNITS = [
    utest_noop,
    utest_noop_args,
    utest_int,
    utest_int_args,
    utest_bytes,
    utest_bytes_args,
    utest_any,
    utest_any_args,
]


@pytest.mark.parametrize("subr, mode", product(UNITS, pt.Mode))
def test_blackbox_pyteal(subr, mode):
    """
    TODO: here's an example of issue #199 at play - (the thread-safety aspect):
    compare the following!
    % pytest -n 2 tests/integration/graviton_test.py::test_blackbox_pyteal
    vs
    % pytest -n 1 tests/integration/graviton_test.py::test_blackbox_pyteal
    """
    is_app = mode == pt.Mode.Application
    name = f"{'app' if is_app else 'lsig'}_{subr.name()}"

    compiled = pt.compileTeal(blackbox_pyteal(subr, mode)(), mode, version=6)
    save_to = TEAL_PATH / (name + ".teal")
    with open(save_to, "w") as f:
        f.write(compiled)

    assert_teal_as_expected(save_to, TEAL_PATH / (name + "_expected.teal"))
