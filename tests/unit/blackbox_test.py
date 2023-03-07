# TODO: add blackbox_test.py to multithreaded tests when following issue has been fixed:
# 	https://github.com/algorand/pyteal/issues/199


from itertools import product
from pathlib import Path
from typing import Literal, Optional, Tuple
from unittest.mock import MagicMock

import pytest
from algosdk.v2client.algod import AlgodClient
from graviton.inspector import DryRunProperty as DRProp

import pyteal as pt
from tests.blackbox import (
    Blackbox,
    BlackboxWrapper,
    PyTealDryRunExecutor,
    RouterSimulation,
)
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


@Blackbox(input_types=[pt.TealType.bytes])
@pt.ABIReturnSubroutine
def fn_1tt_arg_uint64_ret(x, *, output: pt.abi.Uint64) -> pt.Expr:
    return output.set(1)


@Blackbox(input_types=[None, pt.TealType.uint64, None])
@pt.ABIReturnSubroutine
def fn_3mixed_args_0ret(
    a: pt.abi.Uint64, b: pt.ScratchVar, C: pt.abi.StaticArray[pt.abi.Byte, Literal[10]]
) -> pt.Expr:
    return pt.Return()


@Blackbox(input_types=[None, pt.TealType.bytes])
@pt.ABIReturnSubroutine
def fn_2mixed_arg_1ret(
    a: pt.abi.Uint64, b: pt.ScratchVar, *, output: pt.abi.Uint64
) -> pt.Expr:
    return pt.Seq(b.store(a.encode()), output.set(a))


ABI_UNITS = [
    (fn_0arg_0ret, None),
    (fn_0arg_uint64_ret, pt.abi.Uint64()),
    (fn_1arg_0ret, None),
    (fn_1arg_1ret, pt.abi.Uint64()),
    (fn_2arg_0ret, None),
    (fn_1tt_arg_uint64_ret, pt.abi.Uint64()),
    (fn_3mixed_args_0ret, None),
    (fn_2mixed_arg_1ret, pt.abi.Uint64()),
]


# ---- test functions ---- #


@pytest.mark.parametrize("subr, mode", product(UNITS, pt.Mode))
@pytest.mark.serial  # Serial due to scratch generation
def test_blackbox_pyteal(subr: BlackboxWrapper, mode: pt.Mode):
    is_app = mode == pt.Mode.Application
    name = f"{'app' if is_app else 'lsig'}_{subr.name()}"

    compiled = PyTealDryRunExecutor(subr, mode).compile(version=6)
    tealdir = GENERATED / "blackbox"
    tealdir.mkdir(parents=True, exist_ok=True)
    save_to = tealdir / (name + ".teal")
    with open(save_to, "w") as f:
        f.write(compiled)

    assert_teal_as_expected(save_to, FIXTURES / "blackbox" / (name + ".teal"))


@pytest.mark.parametrize("subr_abi, mode", product(ABI_UNITS, pt.Mode))
@pytest.mark.serial  # Serial due to scratch generation
def test_abi_blackbox_pyteal(
    subr_abi: Tuple[BlackboxWrapper, Optional[pt.ast.abi.BaseType]], mode: pt.Mode
):
    subr, abi_return_type = subr_abi
    name = f"{'app' if mode == pt.Mode.Application else 'lsig'}_{subr.name()}"
    print(f"Case {subr.name()=}, {abi_return_type=}, {mode=} ------> {name=}")

    pdre = PyTealDryRunExecutor(subr, mode)
    assert pdre.is_abi(), "should be an ABI subroutine"

    arg_types = pdre.abi_argument_types()
    if subr.name() != "fn_1tt_arg_uint64_ret":
        assert not arg_types or any(
            arg_types
        ), "abi_argument_types() should have had some abi info"

    if abi_return_type:
        expected_sdk_return_type = pt.abi.algosdk_from_type_spec(
            abi_return_type.type_spec()
        )
        assert expected_sdk_return_type == pdre.abi_return_type()
    else:
        assert pdre.abi_return_type() is None

    compiled = pdre.compile(version=6)
    tealdir = GENERATED / "abi"
    tealdir.mkdir(parents=True, exist_ok=True)
    save_to = tealdir / (name + ".teal")
    with open(save_to, "w") as f:
        f.write(compiled)

    assert_teal_as_expected(save_to, FIXTURES / "abi" / (name + ".teal"))


@pytest.mark.parametrize("mode", (pt.Mode.Application, pt.Mode.Signature))
@pytest.mark.parametrize(
    "fn, expected_is_abi", ((utest_noop, False), (fn_0arg_uint64_ret, True))
)
@pytest.mark.serial
def test_PyTealBlackboxExecutor_is_abi(
    mode: pt.Mode, fn: BlackboxWrapper, expected_is_abi: bool
):
    p = PyTealDryRunExecutor(fn, mode)
    assert p.is_abi() == expected_is_abi
    if expected_is_abi:
        assert p.abi_argument_types() is not None
        assert p.abi_return_type() is not None
    else:
        assert p.abi_argument_types() is None
        assert p.abi_return_type() is None


@pytest.mark.parametrize("mode", (pt.Mode.Application, pt.Mode.Signature))
@pytest.mark.parametrize(
    "fn, expected_arg_count",
    (
        (fn_0arg_uint64_ret, 0),
        (fn_1arg_0ret, 1),
        (fn_1arg_1ret, 1),
        (fn_2arg_0ret, 2),
        (fn_2mixed_arg_1ret, 2),
    ),
)
@pytest.mark.serial
def test_PyTealBlackboxExecutor_abi_argument_types(
    mode: pt.Mode, fn: BlackboxWrapper, expected_arg_count: int
):
    actual = PyTealDryRunExecutor(fn, mode).abi_argument_types()
    assert actual is not None
    assert len(actual) == expected_arg_count


@pytest.mark.parametrize("mode", (pt.Mode.Application, pt.Mode.Signature))
@pytest.mark.parametrize(
    "fn, expected_does_produce_type",
    (
        (fn_0arg_uint64_ret, True),
        (fn_1arg_0ret, False),
        (fn_1arg_1ret, True),
        (fn_2arg_0ret, False),
        (fn_2mixed_arg_1ret, True),
    ),
)
@pytest.mark.serial
def test_PyTealBlackboxExecutor_abi_return_type(
    mode: pt.Mode, fn: BlackboxWrapper, expected_does_produce_type: bool
):
    if expected_does_produce_type:
        assert PyTealDryRunExecutor(fn, mode).abi_return_type() is not None
    else:
        assert PyTealDryRunExecutor(fn, mode).abi_return_type() is None


def successful_RouterSimulation(router, model_router, predicates, algod):
    rsim = RouterSimulation(
        router,
        predicates,
        model_router=model_router,
        algod=algod,
    )
    assert rsim.router == router
    assert rsim.predicates == predicates
    assert rsim.model_router == model_router
    assert rsim.algod == algod

    return rsim


def failing_RouterSimulation(router, model_router, predicates, algod, err_msg):
    with pytest.raises(AssertionError) as ae:
        RouterSimulation(
            router,
            predicates,
            model_router=model_router,
            algod=algod,
        )
    assert err_msg == str(ae.value)


def test_RouterSimulation_init():
    router = "not a router"
    model_router = "not a router either"
    predicates = "totally unchecked at init"
    algod = MagicMock(spec=AlgodClient)

    # many paths to misery:
    err_msg = "Wrong type for Base Router: <class 'str'>"
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    router = pt.Router("test_router")
    err_msg = "make sure to give at least one key/value pair in method_configs"
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    router.add_method_handler(
        pt.ABIReturnSubroutine(lambda: pt.Int(1)), overriding_name="foo"
    )
    err_msg = "Wrong type for predicates: <class 'str'>. Please provide: dict[str | None, dict[graviton.DryRunProporty, Any]."
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    predicates = {}
    err_msg = "Please provide at least one method to call and assert against."
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    predicates = {3: "blah"}
    err_msg = "Predicates method '3' has type <class 'int'> but only 'str' and 'NoneType' and Literal['ClearStateCall'] (== ClearStateCall) are allowed."
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    predicates = {Literal[42]: "blah"}
    err_msg = "Predicates method 'typing.Literal[42]' is not allowed. Only Literal['ClearStateCall'] (== ClearStateCall) is allowed for a Literal."
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    predicates = {"bar": {DRProp.passed: True}, "foo": {}}
    err_msg = "Every method must provide at least one predicate for assertion but method 'foo' is missing predicates."
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    predicates = {"bar": {DRProp.passed: True}, "foo": 42}
    err_msg = "Method 'foo' is expected to have dict[graviton.DryRunProperty, Any] for its predicates value but the type is <class 'int'>."
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    predicates = {"bar": {DRProp.passed: True}, "foo": {"blah": 45}}
    err_msg = "Method 'foo' is expected to have dict[graviton.DryRunProperty, Any] for its predicates value but predicates['foo'] has key 'blah' of <class 'str'>."
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    predicates = {"bar": {DRProp.passed: True}, "foo": {DRProp.budgetAdded: 45}}
    err_msg = "Wrong type for Model Router: <class 'str'>"
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    model_router = pt.Router("test_router")
    err_msg = "make sure to give at least one key/value pair in method_configs"
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    # Finally, two happy paths
    model_router.add_method_handler(
        pt.ABIReturnSubroutine(lambda: pt.Int(1)), overriding_name="foo"
    )
    successful_RouterSimulation(router, model_router, predicates, algod)

    model_router = None
    successful_RouterSimulation(router, model_router, predicates, algod)
