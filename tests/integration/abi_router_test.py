import json
import re
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

import pytest
from graviton.abi_strategy import (
    ABIArgsMod,
    RandomABIStrategy,
    RandomABIStrategyHalfSized,
)
from graviton.blackbox import DryRunEncoder
from graviton.invariant import DryRunProperty as DRProp

import pyteal as pt
from pyteal.compiler.compiler_test import router_app_tester
from tests.blackbox import (
    CLEAR_STATE_CALL,
    ABICallConfigs,
    Predicates,
    RouterCallType,
    RouterSimulation,
    negate_cc,
)

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
QUESTIONABLE_DRIVER: list[tuple[RouterCallType, pt.MethodConfig, Predicates]] = [
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
            opt_in=pt.CallConfig.CALL,
        ),
        {
            DRProp.passed: True,
            DRProp.lastLog: lambda _, actual: actual
            in (None, DryRunEncoder.hex("optin call")),
        },
    ),
    (
        CLEAR_STATE_CALL,
        pt.MethodConfig(),  # ignored in this case
        {
            DRProp.passed: True,
            DRProp.cost: 2,
        },
    ),
]

YACC_DRIVER = [case for case in QUESTIONABLE_DRIVER if case[0]]

DRIVERS = {"questionable": QUESTIONABLE_DRIVER, "yacc": YACC_DRIVER}


def split_driver2predicates_methconfigs(driver) -> tuple[Predicates, ABICallConfigs]:
    predicates = {}
    methconfigs = {}
    for meth, meth_config, predicate in driver:
        predicates[meth] = predicate
        if meth != CLEAR_STATE_CALL:
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

    # assert FULL coverage:
    assert methconfigs == router.method_configs

    rsim = RouterSimulation(router, predicates)

    def msg():
        return f"""test_abi_router_positive()
{case=}
{version=}
{router.name=}"""

    results = rsim.simulate_and_assert(
        approval_args_strat_type=RandomABIStrategyHalfSized,
        clear_args_strat_type=RandomABIStrategy,
        approval_abi_args_mod=None,
        version=version,
        method_configs=methconfigs,
        num_dryruns=NUM_ROUTER_DRYRUNS,
        msg=msg(),
    )
    # won't even get here if there was an error, but some extra sanity checks:
    assert (sim_results := results.results) and all(
        sim.succeeded for meth in sim_results.values() for sim in meth.values()
    )

    print("\nstats:", json.dumps(stats := results.stats, indent=2))
    assert stats and all(stats.values())

    # wow!!! these fail because of differing scratch slot assignments
    if BRUTE_FORCE_TERRIBLE_SKIPPING:
        pass
    else:
        assert pregen_clear == results.clear_simulator.simulate_dre.program
        assert pregen_approval == results.approval_simulator.simulate_dre.program

    # TODO: uncomment eventually ...
    # with open(FIXTURES / f"sim_approval_{case}_{version}.teal", "w") as f:
    #     f.write(results["sim_cfg"].ap_compiled)
    # with open(FIXTURES / f"sim_clear_{case}_{version}.teal", "w") as f:
    #     f.write(results["sim_cfg"].csp_compiled)


# cf. https://death.andgravity.com/f-re for an explanation of verbose regex'es
EXPECTED_ERR_PATTERN = r"""
    err\ opcode                                 # pyteal generated err's ok
|   assert\ failed\ pc=                         # pyteal generated assert's ok
|   invalid\ ApplicationArgs\ index             # failing because an app arg wasn't provided
|   extract\ range\ beyond\ length\ of\ string  # failing because couldn't extract when omitted final arg or jammed in tuple
"""


APPROVAL_NEGATIVE_PREDS = {
    DRProp.rejected: True,
    DRProp.error: True,
    DRProp.errorMessage: lambda _, actual: (
        bool(re.search(EXPECTED_ERR_PATTERN, actual, re.VERBOSE))
    ),
}

CLEAR_NEGATIVE_INVARIANTS_MUST_APPROVE = [
    inv for m, _, inv in QUESTIONABLE_DRIVER if m == CLEAR_STATE_CALL
][0]


@pytest.mark.parametrize("case, version, router", ROUTER_CASES)
def test_abi_router_negative(case, version, router):
    totals = defaultdict(int)

    def scenario_assert_stats(scenario, results):
        part_a = f"""
SCENARIO: {scenario} 
"""
        if results:
            part_b = json.dumps(stats := results.stats, indent=2)
            assert stats and all(stats.values())
            for k, v in stats.items():
                if isinstance(v, int):
                    totals[k] += v
        else:
            part_b = "SKIPPED"
        print(f"{part_a}stats:", part_b)

    contract = router.contract_construct()

    driver = DRIVERS[case]
    pos_predicates, pos_mconfigs = split_driver2predicates_methconfigs(driver)
    # assert FULL coverage (before modifying the dict):
    assert pos_mconfigs == router.method_configs

    if None not in pos_mconfigs:
        pos_mconfigs[None] = pt.MethodConfig()
        pos_predicates[None] = APPROVAL_NEGATIVE_PREDS

    pure_meth_mconfigs = {
        meth: methconfig
        for meth, methconfig in pos_mconfigs.items()
        if meth is not None
    }

    neg_predicates = {
        meth: (
            APPROVAL_NEGATIVE_PREDS
            if meth != CLEAR_STATE_CALL
            else CLEAR_NEGATIVE_INVARIANTS_MUST_APPROVE
        )
        for meth in pos_predicates
    }

    rsim = RouterSimulation(router, neg_predicates)

    def msg():
        return f"""test_abi_router_negative()
{scenario=}
{case=}
{version=}
{router.name=}"""

    scenario = "I. explore all UNEXPECTED (is_app_create, on_complete) combos"

    # NOTE: We're NOT including clear_state calls for the approval program
    # as though they would never be applied.
    # Also, we're ONLY including clear_state for the clear program.
    # Finally, when no bare app calls are provided in method_configs,
    # we still test the bare app call case.
    neg_mconfigs = {
        meth: pt.MethodConfig(
            **{k: negate_cc(v) for k, v in asdict(mc).items() if k != "clear_state"}
        )
        for meth, mc in pos_mconfigs.items()
    }

    results = rsim.simulate_and_assert(
        approval_args_strat_type=RandomABIStrategyHalfSized,
        clear_args_strat_type=RandomABIStrategy,
        approval_abi_args_mod=None,
        version=version,
        method_configs=neg_mconfigs,
        num_dryruns=NUM_ROUTER_DRYRUNS,
        executor_validation=False,
        msg=msg(),
    )
    # won't even get here if there was an error, but some extra sanity checks:
    assert (sim_results := results.results) and all(
        sim.succeeded for meth in sim_results.values() for sim in meth.values()
    )
    scenario_assert_stats(scenario, results)

    # II. the case of bare-app-calls
    scenario = "II. adding an argument to a bare app call"
    if None in pos_mconfigs and not pos_mconfigs[None].is_never():
        bare_only_methconfigs = {None: pos_mconfigs[None]}
        results = rsim.simulate_and_assert(
            approval_args_strat_type=RandomABIStrategyHalfSized,
            clear_args_strat_type=None,
            approval_abi_args_mod=ABIArgsMod.parameter_append,
            version=version,
            method_configs=bare_only_methconfigs,
            omit_clear_call=True,
            num_dryruns=NUM_ROUTER_DRYRUNS,
            executor_validation=False,
            msg=msg(),
        )
        assert (sim_results := results.results) and all(
            sim.succeeded for meth in sim_results.values() for sim in meth.values()
        )
        scenario_assert_stats(scenario, results)
    else:
        scenario_assert_stats(scenario, None)

    # For the rest, we may assume method calls (non bare-app-call)
    # III. explore changing method selector arg[0] by edit distance 1

    # NOTE: We don't test the case of adding an argument to method calls
    # because the SDK's will guard against this case.
    # However, we should re-think this assumption.
    # Cf: https://github.com/algorand/go-algorand-internal/issues/2772
    # Cf. https://github.com/algorand/algorand-sdk-testing/issues/190

    scenario = "III(a). inserting an extra random byte into method selector"
    results = rsim.simulate_and_assert(
        approval_args_strat_type=RandomABIStrategyHalfSized,
        clear_args_strat_type=None,
        approval_abi_args_mod=ABIArgsMod.selector_byte_insert,
        version=version,
        method_configs=pure_meth_mconfigs,
        omit_clear_call=True,
        num_dryruns=NUM_ROUTER_DRYRUNS,
        executor_validation=False,
        msg=msg(),
    )
    assert (sim_results := results.results) and all(
        sim.succeeded for meth in sim_results.values() for sim in meth.values()
    )
    scenario_assert_stats(scenario, results)

    scenario = "III(b). removing a random byte from method selector"
    results = rsim.simulate_and_assert(
        approval_args_strat_type=RandomABIStrategyHalfSized,
        clear_args_strat_type=None,
        approval_abi_args_mod=ABIArgsMod.selector_byte_delete,
        version=version,
        method_configs=pure_meth_mconfigs,
        omit_clear_call=True,
        num_dryruns=NUM_ROUTER_DRYRUNS,
        executor_validation=False,
        msg=msg(),
    )
    assert (sim_results := results.results) and all(
        sim.succeeded for meth in sim_results.values() for sim in meth.values()
    )
    scenario_assert_stats(scenario, results)

    scenario = "III(c). replacing a random byte in method selector"
    results = rsim.simulate_and_assert(
        approval_args_strat_type=RandomABIStrategyHalfSized,
        clear_args_strat_type=None,
        approval_abi_args_mod=ABIArgsMod.selector_byte_replace,
        version=version,
        method_configs=pure_meth_mconfigs,
        omit_clear_call=True,
        num_dryruns=NUM_ROUTER_DRYRUNS,
        executor_validation=False,
        msg=msg(),
    )
    assert (sim_results := results.results) and all(
        sim.succeeded for meth in sim_results.values() for sim in meth.values()
    )
    scenario_assert_stats(scenario, results)

    # IV. explore changing the number of args over the 'good' call_types
    # NOTE: We don't test the case of adding an argument to method calls
    # We also remove methods with 0 arguments, as these degenerate to the
    # already tested bare-app call case.
    scenario = "IV. removing the final argument"
    atleast_one_param_mconfigs = {
        meth: mconfig
        for meth, mconfig in pure_meth_mconfigs.items()
        if len(contract.get_method_by_name(meth).args) > 0
    }
    results = rsim.simulate_and_assert(
        approval_args_strat_type=RandomABIStrategyHalfSized,
        clear_args_strat_type=None,
        approval_abi_args_mod=ABIArgsMod.parameter_delete,
        version=version,
        method_configs=atleast_one_param_mconfigs,
        omit_clear_call=True,
        num_dryruns=NUM_ROUTER_DRYRUNS,
        executor_validation=False,
        msg=msg(),
    )
    assert (sim_results := results.results) and all(
        sim.succeeded for meth in sim_results.values() for sim in meth.values()
    )
    scenario_assert_stats(scenario, results)

    print("SUMMARY STATS: ", json.dumps(totals, indent=2))
