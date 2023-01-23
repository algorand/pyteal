from itertools import product
from pathlib import Path
import pytest
from typing import Literal, Optional, Tuple
from unittest.mock import MagicMock

from algosdk.v2client.algod import AlgodClient
from graviton.abi_strategy import ABIArgsMod, RandomABIStrategy
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
    router = MagicMock(spec=pt.Router)
    model_router = MagicMock(spec=pt.Router)
    assert router != model_router

    predicates = "totally unchecked at init"
    algod = MagicMock(spec=AlgodClient)

    err_msg = "Wrong type for predicates: <class 'str'>. Please provide: dict[str | None, dict[graviton.DryRunProporty, Any]."
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    predicates = {}
    err_msg = "Please provide at least one method to call and assert against."
    failing_RouterSimulation(router, model_router, predicates, algod, err_msg)

    predicates = {3: "blah"}
    err_msg = "Predicates method '3' has type <class 'int'> but only 'str' and 'NoneType' are allowed."
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
    successful_RouterSimulation(router, model_router, predicates, algod)


def failing_prep_simulate(
    rsim,
    arg_strat_type,
    abi_args_mod,
    version,
    assemble_constants,
    optimize,
    method_configs,
    num_dryruns,
    txn_params,
    model_version,
    model_assemble_constants,
    model_optimize,
    err_msg,
    err_type=AssertionError,
):
    with pytest.raises(err_type) as ae:
        rsim._prep_simulation(
            arg_strat_type,
            abi_args_mod,
            version,
            assemble_constants=assemble_constants,
            optimize=optimize,
            method_configs=method_configs,
            num_dryruns=num_dryruns,
            txn_params=txn_params,
            model_version=model_version,
            model_assemble_constants=model_assemble_constants,
            model_optimize=model_optimize,
        )
    assert err_msg == str(ae.value)


def get_2meth_router():
    router = pt.Router(
        "router",
        pt.BareCallActions(
            opt_in=pt.OnCompleteAction(
                action=pt.Reject(), call_config=pt.CallConfig.ALL
            ),
        ),
        clear_state=pt.Approve(),
    )

    @router.method
    def m1():
        return pt.Approve()

    @router.method
    def m2():
        return pt.Reject()

    return router


def test_prep_simulation():
    # init params:
    predicates = {
        None: {
            DRProp.rejected: True,
        },
        "m1": {
            DRProp.passed: True,
            DRProp.cost: 42,
        },
        "m2": {
            DRProp.passed: True,
            DRProp.lastLog: "blah blah blah",
        },
    }
    router = pt.Router("empty")
    assert {} == router.method_configs

    model_router = None  # starting out, just test using one router
    algod = MagicMock(spec=AlgodClient)
    rsim = successful_RouterSimulation(router, model_router, predicates, algod)

    # _prep_simulation params. Start with bad ones and fix one-by-one
    arg_strat_type = 25  # WRONG TYPE
    abi_args_mod = 17  # WRONG TYPE
    version = -13  # ASSERTED BY Router.compile()
    assemble_constants = False  # this won't be asserted
    optimize = None  # this won't be asserted
    method_configs = 55  # EITHER NONE OR OF TYPE dict[str, MethodConfig]
    num_dryruns = -100  # MUST BE A POSITIVE NUMBER
    txn_params = "foo foo"  # EITHER NONE OR OF TYPE TxParams
    model_version = -103  # EXISTENCE ASSERTED IN CASE OF model_router
    model_assemble_constants = False  # this won't be asserted
    model_optimize = None  # this won't be asserted

    err_msg = "arg_strat_type should _BE_ a subtype of ABIStrategy but we have 25 (its type is <class 'int'>)."
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    arg_strat_type = int
    err_msg = "arg_strat_type should _BE_ a subtype of ABIStrategy but we have <class 'int'> (its type is <class 'type'>)."
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    arg_strat_type = RandomABIStrategy  # finally fixed
    # but abi_args_mod is still wrong
    err_msg = "abi_args_mod '17' has type <class 'int'> but only 'ABIArgsMod' and 'NoneType' are allowed."
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    abi_args_mod = ABIArgsMod.selector_byte_insert  # finally fixed
    # but version is still wrong
    err_msg = f"Unsupported program version: -13. Excepted an integer in the range [2, {pt.MAX_PROGRAM_VERSION}]"
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
        err_type=pt.TealInputError,
    )

    version = 7  # finally fixed
    err_msg = "Base router with name 'empty' is essentially empty, as compilation results in an empty method_configs."
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    router = get_2meth_router()
    router_method_configs = {
        None: pt.MethodConfig(opt_in=pt.CallConfig.ALL),
        "m1": pt.MethodConfig(no_op=pt.CallConfig.CALL),
        "m2": pt.MethodConfig(no_op=pt.CallConfig.CALL),
    }
    assert router_method_configs == router.method_configs
    rsim = successful_RouterSimulation(router, model_router, predicates, algod)

    err_msg = "method_configs '55' has type <class 'int'> but only 'dict' and 'NoneType' are allowed."
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    method_configs = {}
    err_msg = "if providing explicit method_configs, make sure to give at least one"
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    method_configs = {
        None: pt.MethodConfig(opt_in=pt.CallConfig.ALL),
        42: "foo",
        "m2": pt.MethodConfig(no_op=pt.CallConfig.ALL),
    }
    err_msg = "method_configs dict key '42' has type <class 'int'> but only str and NoneType are allowed."
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    method_configs = {
        None: pt.MethodConfig(opt_in=pt.CallConfig.ALL),
        "m1": "foo",
        "m2": pt.MethodConfig(no_op=pt.CallConfig.ALL),
    }
    err_msg = "method_configs['m1'] = has type <class 'str'> but only MethodConfig is allowed."
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    method_configs = {
        None: pt.MethodConfig(opt_in=pt.CallConfig.ALL),
        "m1": pt.MethodConfig(no_op=pt.CallConfig.CALL),
        "m2": pt.MethodConfig(no_op=pt.CallConfig.NEVER),
    }
    err_msg = "method_configs['m2'] specifies NEVER to be called; for driving the test, each configured method should ACTUALLY be tested."
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    method_configs = router_method_configs  # finally fixed
    # but num_dry_runs is still illegal
    err_msg = "num_dryruns must be a positive int but is -100."
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    num_dryruns = 4  # finally fixed
    # but txn_params is still messed up
    err_msg = "txn_params must have type DryRunTransactionParams or NoneType but has type <class 'str'>."
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    txn_params = None  # finally fixed
    # but shoudn't provide `model_*` params when `model_router` wasn't provided
    err_msg = "model_version '-103' was provided which is nonsensical because model_router was never provided for."
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
    )

    # -- NOW TRY model_router AS WELL -- #
    model_router = router
    algod = MagicMock(spec=AlgodClient)
    rsim = successful_RouterSimulation(router, model_router, predicates, algod)
    # but model_version is still wrong
    err_msg = f"Unsupported program version: -103. Excepted an integer in the range [2, {pt.MAX_PROGRAM_VERSION}]"
    failing_prep_simulate(
        rsim,
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants,
        optimize,
        method_configs,
        num_dryruns,
        txn_params,
        model_version,
        model_assemble_constants,
        model_optimize,
        err_msg,
        err_type=pt.TealInputError,
    )

    model_version = 8  # FINALLY FINALLY FINALLY FIXED
    # OK! we should be GTG

    sim_cfg = rsim._prep_simulation(
        arg_strat_type,
        abi_args_mod,
        version,
        assemble_constants=assemble_constants,
        optimize=optimize,
        method_configs=method_configs,
        num_dryruns=num_dryruns,
        txn_params=txn_params,
        model_version=model_version,
        model_assemble_constants=model_assemble_constants,
        model_optimize=model_optimize,
    )
    assert sim_cfg.version == version
    assert sim_cfg.assemble_constants == assemble_constants
    assert sim_cfg.optimize == optimize

    assert sim_cfg.ap_compiled
    assert sim_cfg.csp_compiled
    assert sim_cfg.contract

    assert sim_cfg.method_configs == method_configs

    assert sim_cfg.call_strat
    assert sim_cfg.call_strat.abi_args_mod == abi_args_mod

    assert sim_cfg.txn_params == txn_params

    assert sim_cfg.model_version == model_version
    assert sim_cfg.model_assemble_constants == model_assemble_constants
    assert sim_cfg.model_optimize == model_optimize

    assert sim_cfg.model_ap_compiled
    assert sim_cfg.model_csp_compiled
    assert sim_cfg.model_contract
