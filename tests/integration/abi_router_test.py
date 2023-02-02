import json
from pathlib import Path
import pytest

from graviton.abi_strategy import RandomABIStrategyHalfSized
from graviton.blackbox import DryRunEncoder
from graviton.invariant import DryRunProperty as DRProp

from pyteal.compiler.compiler_test import router_app_tester
import pyteal as pt

from tests.blackbox import Predicates, RouterSimulation

BRUTE_FORCE_TERRIBLE_SKIPPING = True
NUM_ROUTER_DRYRUNS = 7
FIXTURES = Path.cwd() / "tests" / "teal" / "router"


ROUTER_CASES, ROUTER_SOURCES = router_app_tester()

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
            # clear_state=pt.CallConfig.CALL,
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
            # clear_state=pt.CallConfig.CALL,
        ),
        {DRProp.passed: True, DRProp.lastLog: 1},
    ),
    (
        "log_creation",
        pt.MethodConfig(no_op=pt.CallConfig.CREATE),
        {DRProp.passed: True, DRProp.lastLog: "logging creation"},
    ),
    (
        None,
        pt.MethodConfig(
            opt_in=pt.CallConfig.CALL,  # clear_state=pt.CallConfig.CALL
        ),
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

    # wow!!! these fail because of differing scratch slot assignments
    if BRUTE_FORCE_TERRIBLE_SKIPPING:
        pass
    else:
        assert pregen_approval == results["approval_simulator"].simulate_dre.program
        assert pregen_clear == results["clear_simulator"].simulate_dre.program

    with open(FIXTURES / f"sim_approval_{case}_{version}.teal", "w") as f:
        f.write(results["sim_cfg"].ap_compiled)
    with open(FIXTURES / f"sim_clear_{case}_{version}.teal", "w") as f:
        f.write(results["sim_cfg"].csp_compiled)
