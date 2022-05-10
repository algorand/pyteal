from itertools import product
from pathlib import Path
import pytest
from typing import Literal

import pyteal as pt

from tests.blackbox import Blackbox, blackbox_pyteal

from tests.compile_asserts import assert_teal_as_expected

PATH = Path.cwd() / "tests" / "unit"
FIXTURES = PATH / "teal"
GENERATED = PATH / "generated"

# ---- Subroutine Unit Test Examples ---- #


@Blackbox(input_types=[])
@pt.Subroutine(pt.TealType.none)
def utest_noop():
    return pt.Pop(pt.Int(0))


@Blackbox(input_types=[pt.TealType.uint64, pt.TealType.bytes, pt.TealType.anytype])
@pt.Subroutine(pt.TealType.none)
def utest_noop_args(x, y, z):
    return pt.Pop(pt.Int(0))


@Blackbox(input_types=[])
@pt.Subroutine(pt.TealType.uint64)
def utest_int():
    return pt.Int(0)


@Blackbox(input_types=[pt.TealType.uint64, pt.TealType.bytes, pt.TealType.anytype])
@pt.Subroutine(pt.TealType.uint64)
def utest_int_args(x, y, z):
    return pt.Int(0)


@Blackbox(input_types=[])
@pt.Subroutine(pt.TealType.bytes)
def utest_bytes():
    return pt.Bytes("")


@Blackbox(input_types=[pt.TealType.uint64, pt.TealType.bytes, pt.TealType.anytype])
@pt.Subroutine(pt.TealType.bytes)
def utest_bytes_args(x, y, z):
    return pt.Bytes("")


@Blackbox(input_types=[])
@pt.Subroutine(pt.TealType.anytype)
def utest_any():
    x = pt.ScratchVar(pt.TealType.anytype)
    return pt.Seq(x.store(pt.Int(0)), x.load())


@Blackbox(input_types=[pt.TealType.uint64, pt.TealType.bytes, pt.TealType.anytype])
@pt.Subroutine(pt.TealType.anytype)
def utest_any_args(x, y, z):
    x = pt.ScratchVar(pt.TealType.anytype)
    return pt.Seq(x.store(pt.Int(0)), x.load())


# ---- ABI Return Subroutine Unit Test Examples ---- #


@Blackbox(input_types=[])
@pt.ABIReturnSubroutine
def fn_0arg_0ret() -> pt.Expr:
    return pt.Return()


@Blackbox(input_types=[])
@pt.ABIReturnSubroutine
def fn_0arg_uint64_ret(*, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(1)


@Blackbox(input_types=[None])
@pt.ABIReturnSubroutine
def fn_1arg_0ret(a: pt.abi.Uint64) -> pt.Expr:
    return pt.Return()


@Blackbox(input_types=[None])
@pt.ABIReturnSubroutine
def fn_1arg_1ret(a: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(a)


@Blackbox(input_types=[None, None])
@pt.ABIReturnSubroutine
def fn_2arg_0ret(
    a: pt.abi.Uint64, b: pt.abi.StaticArray[pt.abi.Byte, Literal[10]]
) -> pt.Expr:
    return pt.Return()


@Blackbox(input_types=[None, None])
@pt.ABIReturnSubroutine
def fn_3mixed_args_0ret(
    a: pt.abi.Uint64, b: pt.ScratchVar, C: pt.abi.StaticArray[pt.abi.Byte, Literal[10]]
) -> pt.Expr:
    return pt.Return()


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


ABI_UNITS = [
    fn_0arg_0ret,
    fn_0arg_uint64_ret,
    fn_1arg_0ret,
    fn_1arg_1ret,
    fn_2arg_0ret,
    fn_3mixed_args_0ret,
]


@pytest.mark.parametrize("subr, mode", product(UNITS, pt.Mode))
def test_blackbox_pyteal(subr, mode):
    is_app = mode == pt.Mode.Application
    name = f"{'app' if is_app else 'lsig'}_{subr.name()}"

    compiled = pt.compileTeal(blackbox_pyteal(subr, mode)(), mode, version=6)
    tealdir = GENERATED / "blackbox"
    tealdir.mkdir(parents=True, exist_ok=True)
    save_to = tealdir / (name + ".teal")
    with open(save_to, "w") as f:
        f.write(compiled)

    assert_teal_as_expected(save_to, FIXTURES / "blackbox" / (name + ".teal"))


@pytest.mark.parametrize("subr, mode", product(UNITS, pt.Mode))
def test_abi_blackbox_pyteal(subr, mode):
    is_app = mode == pt.Mode.Application
    name = f"{'app' if is_app else 'lsig'}_{subr.name()}"

    compiled = pt.compileTeal(blackbox_pyteal(subr, mode)(), mode, version=6)
    tealdir = GENERATED / "blackbox"
    tealdir.mkdir(parents=True, exist_ok=True)
    save_to = tealdir / (name + ".teal")
    with open(save_to, "w") as f:
        f.write(compiled)

    assert_teal_as_expected(save_to, FIXTURES / "blackbox" / (name + ".teal"))
