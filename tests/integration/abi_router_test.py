import json
from pathlib import Path
import pytest

from graviton.abi_strategy import RandomABIStrategyHalfSized
from graviton.blackbox import DryRunEncoder
from graviton.invariant import DryRunProperty as DRProp

import pyteal as pt

from tests.blackbox import Predicates, RouterSimulation

NUM_ROUTER_DRYRUNS = 7
FIXTURES = Path.cwd() / "tests" / "integration" / "teal" / "router"


def add_methods_to_router(router: pt.Router):
    @pt.ABIReturnSubroutine
    def add(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(a.get() + b.get())

    meth = router.add_method_handler(add)
    assert meth.method_signature() == "add(uint64,uint64)uint64"

    @pt.ABIReturnSubroutine
    def sub(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(a.get() - b.get())

    meth = router.add_method_handler(sub)
    assert meth.method_signature() == "sub(uint64,uint64)uint64"

    @pt.ABIReturnSubroutine
    def mul(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(a.get() * b.get())

    meth = router.add_method_handler(mul)
    assert meth.method_signature() == "mul(uint64,uint64)uint64"

    @pt.ABIReturnSubroutine
    def div(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(a.get() / b.get())

    meth = router.add_method_handler(div)
    assert meth.method_signature() == "div(uint64,uint64)uint64"

    @pt.ABIReturnSubroutine
    def mod(a: pt.abi.Uint64, b: pt.abi.Uint64, *, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(a.get() % b.get())

    meth = router.add_method_handler(mod)
    assert meth.method_signature() == "mod(uint64,uint64)uint64"

    @pt.ABIReturnSubroutine
    def all_laid_to_args(
        _a: pt.abi.Uint64,
        _b: pt.abi.Uint64,
        _c: pt.abi.Uint64,
        _d: pt.abi.Uint64,
        _e: pt.abi.Uint64,
        _f: pt.abi.Uint64,
        _g: pt.abi.Uint64,
        _h: pt.abi.Uint64,
        _i: pt.abi.Uint64,
        _j: pt.abi.Uint64,
        _k: pt.abi.Uint64,
        _l: pt.abi.Uint64,
        _m: pt.abi.Uint64,
        _n: pt.abi.Uint64,
        _o: pt.abi.Uint64,
        _p: pt.abi.Uint64,
        *,
        output: pt.abi.Uint64,
    ):
        return output.set(
            _a.get()
            + _b.get()
            + _c.get()
            + _d.get()
            + _e.get()
            + _f.get()
            + _g.get()
            + _h.get()
            + _i.get()
            + _j.get()
            + _k.get()
            + _l.get()
            + _m.get()
            + _n.get()
            + _o.get()
            + _p.get()
        )

    meth = router.add_method_handler(all_laid_to_args)
    assert (
        meth.method_signature()
        == "all_laid_to_args(uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64,uint64)uint64"
    )

    @pt.ABIReturnSubroutine
    def empty_return_subroutine() -> pt.Expr:
        return pt.Log(pt.Bytes("appear in both approval and clear state"))

    meth = router.add_method_handler(
        empty_return_subroutine,
        method_config=pt.MethodConfig(
            no_op=pt.CallConfig.CALL,
            opt_in=pt.CallConfig.ALL,
            clear_state=pt.CallConfig.CALL,
        ),
    )
    assert meth.method_signature() == "empty_return_subroutine()void"

    @pt.ABIReturnSubroutine
    def log_1(*, output: pt.abi.Uint64) -> pt.Expr:
        return output.set(1)

    meth = router.add_method_handler(
        log_1,
        method_config=pt.MethodConfig(
            no_op=pt.CallConfig.CALL,
            opt_in=pt.CallConfig.CALL,
            clear_state=pt.CallConfig.CALL,
        ),
    )

    assert meth.method_signature() == "log_1()uint64"

    @pt.ABIReturnSubroutine
    def log_creation(*, output: pt.abi.String) -> pt.Expr:
        return output.set("logging creation")

    meth = router.add_method_handler(
        log_creation, method_config=pt.MethodConfig(no_op=pt.CallConfig.CREATE)
    )
    assert meth.method_signature() == "log_creation()string"

    @pt.ABIReturnSubroutine
    def approve_if_odd(condition_encoding: pt.abi.Uint32) -> pt.Expr:
        return (
            pt.If(condition_encoding.get() % pt.Int(2))
            .Then(pt.Approve())
            .Else(pt.Reject())
        )

    meth = router.add_method_handler(
        approve_if_odd,
        method_config=pt.MethodConfig(
            no_op=pt.CallConfig.NEVER, clear_state=pt.CallConfig.CALL
        ),
    )
    assert meth.method_signature() == "approve_if_odd(uint32)void"


def generate_and_test_routers() -> tuple[str, int, pt.Router, str, str]:
    routers = []
    sources = {}

    def append_router_info(rinfo, programs):
        assert len(rinfo) == 3
        assert len(programs) == 2
        routers.append(rinfo)
        sources[rinfo[:2]] = programs

    # V6 not ready for Frame Pointers:
    on_completion_actions = pt.BareCallActions(
        opt_in=pt.OnCompleteAction.call_only(pt.Log(pt.Bytes("optin call"))),
        clear_state=pt.OnCompleteAction.call_only(pt.Approve()),
    )
    with pytest.raises(pt.TealInputError) as e:
        pt.Router("will-error", on_completion_actions).compile_program(
            version=6, optimize=pt.OptimizeOptions(frame_pointers=True)
        )
    assert "Frame pointers aren't available" in str(e.value)

    # QUESTIONABLE V6:
    _router_with_oc = pt.Router(
        "ASimpleQuestionablyRobustContract", on_completion_actions
    )
    add_methods_to_router(_router_with_oc)
    (
        actual_ap_with_oc_compiled,
        actual_csp_with_oc_compiled,
        _,
    ) = _router_with_oc.compile_program(version=6)
    with open(FIXTURES / "questionable_approval_v6.teal") as f:
        expected_ap_with_oc = f.read()
    with open(FIXTURES / "questionable_clear_v6.teal") as f:
        expected_csp_with_oc = f.read()
    assert expected_ap_with_oc == actual_ap_with_oc_compiled
    assert expected_csp_with_oc == actual_csp_with_oc_compiled
    append_router_info(
        (
            "questionable",
            6,
            _router_with_oc,
        ),
        (
            actual_ap_with_oc_compiled,
            actual_csp_with_oc_compiled,
        ),
    )

    # YACC V6:
    _router_without_oc = pt.Router("yetAnotherContractConstructedFromRouter")
    add_methods_to_router(_router_without_oc)
    (
        actual_ap_without_oc_compiled,
        actual_csp_without_oc_compiled,
        _,
    ) = _router_without_oc.compile_program(version=6)
    with open(FIXTURES / "yacc_approval_v6.teal") as f:
        expected_ap_without_oc = f.read()
    with open(FIXTURES / "yacc_clear_v6.teal") as f:
        expected_csp_without_oc = f.read()
    assert actual_ap_without_oc_compiled == expected_ap_without_oc
    assert actual_csp_without_oc_compiled == expected_csp_without_oc
    append_router_info(
        (
            "yacc",
            6,
            _router_without_oc,
        ),
        (
            actual_ap_without_oc_compiled,
            actual_csp_without_oc_compiled,
        ),
    )

    # QUESTIONABLE FP V8:
    _router_with_oc = pt.Router(
        "QuestionableRouterGenerateCodeWithFramePointer", on_completion_actions
    )
    add_methods_to_router(_router_with_oc)
    (
        actual_ap_with_oc_compiled,
        actual_csp_with_oc_compiled,
        _,
    ) = _router_with_oc.compile_program(version=8)
    with open(FIXTURES / "questionableFP_approval_v8.teal") as f:
        expected_ap_with_oc = f.read()
    with open(FIXTURES / "questionableFP_clear_v8.teal") as f:
        expected_csp_with_oc = f.read()
    assert actual_ap_with_oc_compiled == expected_ap_with_oc
    assert actual_csp_with_oc_compiled == expected_csp_with_oc
    append_router_info(
        (
            "questionable",
            8,
            _router_with_oc,
        ),
        (
            actual_ap_with_oc_compiled,
            actual_csp_with_oc_compiled,
        ),
    )

    # YACC FP V8:
    _router_without_oc = pt.Router(
        "yetAnotherContractConstructedFromRouterWithFramePointer"
    )
    add_methods_to_router(_router_without_oc)
    (
        actual_ap_without_oc_compiled,
        actual_csp_without_oc_compiled,
        _,
    ) = _router_without_oc.compile_program(version=8)
    with open(FIXTURES / "yaccFP_approval_v8.teal") as f:
        expected_ap_without_oc = f.read()
    with open(FIXTURES / "yaccFP_clear_v8.teal") as f:
        expected_csp_without_oc = f.read()
    assert actual_ap_without_oc_compiled == expected_ap_without_oc
    assert actual_csp_without_oc_compiled == expected_csp_without_oc
    append_router_info(
        (
            "yacc",
            8,
            _router_without_oc,
        ),
        (
            actual_ap_without_oc_compiled,
            actual_csp_without_oc_compiled,
        ),
    )

    return routers, sources


ROUTER_CASES, ROUTER_SOURCES = generate_and_test_routers()

TYPICAL_IAC_OC = pt.MethodConfig(no_op=pt.CallConfig.CALL)

# TEST DRIVERS LEGEND - combines method_configs + predicates
# * @0 - method: str. method == `None` indicates bare app call
#
# * @1 - method_config: MethodConfig - defines how to call the method
#
# * @3 - predicates: Predicates ~ dict[DRProp, Any]
#   these are being asserted after being processed into Invariant's
#
# NOTE: the "yacc" routers will simply ignore the case with method `None`
# as they do not have any bare-app-calls
QUESTIONABLE_DRIVER: list[tuple[str | None, pt.MethodConfig, Predicates]] = [
    (
        "add",
        TYPICAL_IAC_OC,
        {DRProp.passed: True, DRProp.lastLog: lambda args: args[1] + args[2]},
    ),
    (
        "sub",
        TYPICAL_IAC_OC,
        {
            DRProp.passed: lambda args: args[1] >= args[2],
            DRProp.lastLog: (
                lambda args, actual: True
                if args[1] < args[2]
                else actual == args[1] - args[2]
            ),
        },
    ),
    (
        "mul",
        TYPICAL_IAC_OC,
        {DRProp.passed: True, DRProp.lastLog: lambda args: args[1] * args[2]},
    ),
    (
        "div",
        TYPICAL_IAC_OC,
        {DRProp.passed: True, DRProp.lastLog: lambda args: args[1] // args[2]},
    ),
    (
        "mod",
        TYPICAL_IAC_OC,
        {DRProp.passed: True, DRProp.lastLog: lambda args: args[1] % args[2]},
    ),
    (
        "all_laid_to_args",
        TYPICAL_IAC_OC,
        {DRProp.passed: True, DRProp.lastLog: lambda args: sum(args[1:])},
    ),
    (
        "empty_return_subroutine",
        pt.MethodConfig(
            no_op=pt.CallConfig.CALL,
            opt_in=pt.CallConfig.ALL,
            clear_state=pt.CallConfig.CALL,
        ),
        {
            DRProp.passed: True,
            DRProp.lastLog: DryRunEncoder.hex(
                "appear in both approval and clear state"
            ),
        },
    ),
    (
        "log_1",
        pt.MethodConfig(
            no_op=pt.CallConfig.CALL,
            opt_in=pt.CallConfig.CALL,
            clear_state=pt.CallConfig.CALL,
        ),
        {DRProp.passed: True, DRProp.lastLog: 1},
    ),
    (
        "log_creation",
        pt.MethodConfig(no_op=pt.CallConfig.CREATE),
        {DRProp.passed: True, DRProp.lastLog: "logging creation"},
    ),
    (
        "approve_if_odd",  # this should only appear in the clear-state program
        pt.MethodConfig(clear_state=pt.CallConfig.CALL),
        {
            DRProp.passed: lambda args: args[1] % 2 == 1,
            DRProp.lastLog: None,
        },
    ),
    (
        None,
        pt.MethodConfig(opt_in=pt.CallConfig.CALL, clear_state=pt.CallConfig.CALL),
        {
            DRProp.passed: True,
            DRProp.lastLog: lambda _, actual: actual
            in (None, DryRunEncoder.hex("optin call")),
        },
    ),
]

YACC_DRIVER = [case for case in QUESTIONABLE_DRIVER if case[0]]

DRIVERS = {"questionable": QUESTIONABLE_DRIVER, "yacc": YACC_DRIVER}


def split_driver2predicates_methconfigs(driver):
    predicates = {}
    methconfigs = {}
    for meth, meth_config, predicate in driver:
        predicates[meth] = predicate
        methconfigs[meth] = meth_config

    return predicates, methconfigs


@pytest.mark.parametrize("case, version, router", ROUTER_CASES)
def test_abi_router_positive(case, version, router):
    """
    Test the _positive_ version of a case. In other words, ensure that for each
    router encountered and its driver, iterate through the driver as follows:
        * consider each method or bare call
        * consider each (OnComplete, CallConfig) combination
        * assert that all predicates hold for this call
    """
    pregen_approval, pregen_clear = ROUTER_SOURCES[(case, version)]

    driver = DRIVERS[case]
    predicates, methconfigs = split_driver2predicates_methconfigs(driver)
    assert methconfigs == router.method_configs
    rsim = RouterSimulation(router, predicates)

    def msg():
        return f"""test_abi_router_positive()
{case=}
{version=}
{router.name=}"""

    results = rsim.simulate_and_assert(
        RandomABIStrategyHalfSized,
        abi_args_mod=None,
        version=version,
        num_dryruns=NUM_ROUTER_DRYRUNS,
        msg=msg(),
    )
    # won't even get here if there was an error, but some extra sanity checks:

    assert (sim_results := results["results"]) and all(
        sim.succeeded for meth in sim_results.values() for sim in meth.values()
    )

    print(json.dumps(stats := results["stats"], indent=2))
    assert stats and all(stats.values())

    # wow!!! these fail because of label assignment non-determinism:
    # assert pregen_approval == results["approval_simulator"].simulate_dre.program
    # assert pregen_clear == results["clear_simulator"].simulate_dre.program
    with open(FIXTURES / f"sim_approval_{case}_{version}.teal", "w") as f:
        f.write(results["sim_cfg"].ap_compiled)

    with open(FIXTURES / f"sim_clear_{case}_{version}.teal", "w") as f:
        f.write(results["sim_cfg"].csp_compiled)
