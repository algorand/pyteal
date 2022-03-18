import os
from pathlib import Path
from itertools import product
from typing import Dict, Tuple

import pytest

from .compile_asserts import assert_teal_as_expected
from .semantic_asserts import (
    algod_with_assertion,
    get_blackbox_scenario_components,
    e2e_pyteal,
    mode_has_assertion,
)

from algosdk.testing.dryrun import Helper as DryRunHelper
from algosdk.testing.teal_blackbox import (
    DryRunAssertionType as DRA,
    SequenceAssertion,
    csv_from_dryruns,
    dryrun_assert,
    lightly_encode_args,
    lightly_encode_output,
    scratch_encode,
)

from pyteal import *

# TODO: get tests working on github and set this to True
SEMANTIC_TESTING = os.environ.get("HAS_ALGOD") == "TRUE"
# TODO: remove these skips after the following issue has been fixed https://github.com/algorand/pyteal/issues/199
STABLE_SLOT_GENERATION = False
SKIP_SCRATCH_ASSERTIONS = not STABLE_SLOT_GENERATION


####### Subroutine Definitions Being Tested ########


@Subroutine(TealType.uint64, input_types=[])
def exp():
    return Int(2) ** Int(10)


@Subroutine(TealType.none, input_types=[TealType.uint64])
def square_byref(x: ScratchVar):
    return x.store(x.load() * x.load())


@Subroutine(TealType.uint64, input_types=[TealType.uint64])
def square(x):
    return x ** Int(2)


@Subroutine(TealType.none, input_types=[TealType.anytype, TealType.anytype])
def swap(x: ScratchVar, y: ScratchVar):
    z = ScratchVar(TealType.anytype)
    return Seq(
        z.store(x.load()),
        x.store(y.load()),
        y.store(z.load()),
    )


@Subroutine(TealType.bytes, input_types=[TealType.bytes, TealType.uint64])
def string_mult(s: ScratchVar, n):
    i = ScratchVar(TealType.uint64)
    tmp = ScratchVar(TealType.bytes)
    start = Seq(i.store(Int(1)), tmp.store(s.load()), s.store(Bytes("")))
    step = i.store(i.load() + Int(1))
    return Seq(
        For(start, i.load() <= n, step).Do(s.store(Concat(s.load(), tmp.load()))),
        s.load(),
    )


@Subroutine(TealType.uint64, input_types=[TealType.uint64])
def oldfac(n):
    return If(n < Int(2)).Then(Int(1)).Else(n * oldfac(n - Int(1)))


@Subroutine(TealType.uint64, input_types=[TealType.uint64])
def slow_fibonacci(n):
    return (
        If(n <= Int(1))
        .Then(n)
        .Else(slow_fibonacci(n - Int(2)) + slow_fibonacci(n - Int(1)))
    )


def fac_with_overflow(n):
    if n < 2:
        return 1
    if n > 20:
        return 2432902008176640000
    return n * fac_with_overflow(n - 1)


def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fib_cost(args):
    cost = 17
    for n in range(1, args[0] + 1):
        cost += 31 * fib(n - 1)
    return cost


APP_SCENARIOS = {
    exp: {
        "inputs": [()],
        # since only a single input, just assert a constant in each case
        "assertions": {
            DRA.cost: 11,
            # int assertions on log outputs need encoding to varuint-hex:
            DRA.lastLog: lightly_encode_output(2 ** 10, logs=True),
            # dicts have a special meaning as assertions. So in the case of "finalScratch"
            # which is supposed to _ALSO_ output a dict, we need to use a lambda as a work-around
            DRA.finalScratch: lambda _: {0: 1024},
            DRA.stackTop: 1024,
            DRA.maxStackHeight: 2,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    square_byref: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRA.cost: lambda _, actual: 20 < actual < 22,
            DRA.lastLog: lightly_encode_output(1337, logs=True),
            # due to dry-run artifact of not reporting 0-valued scratchvars,
            # we have a special case for n=0:
            DRA.finalScratch: lambda args, actual: (
                {1, 1337, (args[0] ** 2 if args[0] else 1)}
            ).issubset(set(actual.values())),
            DRA.stackTop: 1337,
            DRA.maxStackHeight: 3,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    square: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRA.cost: 14,
            DRA.lastLog: {
                # since execution REJECTS for 0, expect last log for this case to be None
                (i,): lightly_encode_output(i * i, logs=True) if i else None
                for i in range(100)
            },
            DRA.finalScratch: lambda args: (
                {0: args[0] ** 2, 1: args[0]} if args[0] else {}
            ),
            DRA.stackTop: lambda args: args[0] ** 2,
            DRA.maxStackHeight: 2,
            DRA.status: lambda i: "PASS" if i[0] > 0 else "REJECT",
            DRA.passed: lambda i: i[0] > 0,
            DRA.rejected: lambda i: i[0] == 0,
            DRA.noError: True,
        },
    },
    swap: {
        "inputs": [(1, 2), (1, "two"), ("one", 2), ("one", "two")],
        "assertions": {
            DRA.cost: 27,
            DRA.lastLog: lightly_encode_output(1337, logs=True),
            DRA.finalScratch: lambda args: {
                0: 1337,
                1: scratch_encode(args[1]),
                2: scratch_encode(args[0]),
                3: 1,
                4: 2,
                5: scratch_encode(args[0]),
            },
            DRA.stackTop: 1337,
            DRA.maxStackHeight: 2,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    string_mult: {
        "inputs": [("xyzw", i) for i in range(100)],
        "assertions": {
            DRA.cost: lambda args: 30 + 15 * args[1],
            DRA.lastLog: (
                lambda args: lightly_encode_output(args[0] * args[1])
                if args[1]
                else None
            ),
            # due to dryrun 0-scratchvar artifact, special case for i == 0:
            DRA.finalScratch: lambda args: (
                {
                    0: scratch_encode(args[0] * args[1]),
                    1: scratch_encode(args[0] * args[1]),
                    2: 1,
                    3: args[1],
                    4: args[1] + 1,
                    5: scratch_encode(args[0]),
                }
                if args[1]
                else {
                    2: 1,
                    4: args[1] + 1,
                    5: scratch_encode(args[0]),
                }
            ),
            DRA.stackTop: lambda args: len(args[0] * args[1]),
            DRA.maxStackHeight: lambda args: 3 if args[1] else 2,
            DRA.status: lambda args: ("PASS" if 0 < args[1] < 45 else "REJECT"),
            DRA.passed: lambda args: 0 < args[1] < 45,
            DRA.rejected: lambda args: 0 >= args[1] or args[1] >= 45,
            DRA.noError: True,
        },
    },
    oldfac: {
        "inputs": [(i,) for i in range(25)],
        "assertions": {
            DRA.cost: lambda args, actual: (actual - 40 <= 17 * args[0] <= actual + 40),
            DRA.lastLog: lambda args: (
                lightly_encode_output(fac_with_overflow(args[0]), logs=True)
                if args[0] < 21
                else None
            ),
            DRA.finalScratch: lambda args: (
                {1: args[0], 0: fac_with_overflow(args[0])}
                if 0 < args[0] < 21
                else (
                    {1: min(21, args[0])}
                    if args[0]
                    else {0: fac_with_overflow(args[0])}
                )
            ),
            DRA.stackTop: lambda args: fac_with_overflow(args[0]),
            DRA.maxStackHeight: lambda args: max(2, 2 * args[0]),
            DRA.status: lambda args: "PASS" if args[0] < 21 else "REJECT",
            DRA.passed: lambda args: args[0] < 21,
            DRA.rejected: lambda args: args[0] >= 21,
            DRA.noError: lambda args, actual: (
                actual is True if args[0] < 21 else "overflowed" in actual
            ),
        },
    },
    slow_fibonacci: {
        "inputs": [(i,) for i in range(18)],
        "assertions": {
            DRA.cost: lambda args: (fib_cost(args) if args[0] < 17 else 70_000),
            DRA.lastLog: lambda args: (
                lightly_encode_output(fib(args[0]), logs=True)
                if 0 < args[0] < 17
                else None
            ),
            DRA.finalScratch: lambda args, actual: (
                actual == {1: args[0], 0: fib(args[0])}
                if 0 < args[0] < 17
                else (True if args[0] >= 17 else actual == {})
            ),
            # we declare to "not care" about the top of the stack for n >= 17
            DRA.stackTop: lambda args, actual: (
                actual == fib(args[0]) if args[0] < 17 else True
            ),
            # similarly, we don't care about max stack height for n >= 17
            DRA.maxStackHeight: lambda args, actual: (
                actual == max(2, 2 * args[0]) if args[0] < 17 else True
            ),
            DRA.status: lambda args: "PASS" if 0 < args[0] < 8 else "REJECT",
            DRA.passed: lambda args: 0 < args[0] < 8,
            DRA.rejected: lambda args: 0 >= args[0] or args[0] >= 8,
            DRA.noError: lambda args, actual: (
                actual is True
                if args[0] < 17
                else "dynamic cost budget exceeded" in actual
            ),
        },
    },
}

# NOTE: logic sig dry runs are missing some information when compared with app dry runs.
# Therefore, certain assertions don't make sense for logic sigs explaining why some of the below are commented out:
LOGICSIG_SCENARIOS = {
    exp: {
        "inputs": [()],
        "assertions": {
            # DRA.cost: 11,
            # DRA.lastLog: lightly_encode_output(2 ** 10, logs=True),
            DRA.finalScratch: lambda _: {},
            DRA.stackTop: 1024,
            DRA.maxStackHeight: 2,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    square_byref: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            # DRA.cost: lambda _, actual: 20 < actual < 22,
            # DRA.lastLog: lightly_encode_output(1337, logs=True),
            # due to dry-run artifact of not reporting 0-valued scratchvars,
            # we have a special case for n=0:
            DRA.finalScratch: lambda args: (
                {0: 1, 1: args[0] ** 2} if args[0] else {0: 1}
            ),
            DRA.stackTop: 1337,
            DRA.maxStackHeight: 3,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    square: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            # DRA.cost: 14,
            # DRA.lastLog: {(i,): lightly_encode_output(i * i, logs=True) if i else None for i in range(100)},
            DRA.finalScratch: lambda args: ({0: args[0]} if args[0] else {}),
            DRA.stackTop: lambda args: args[0] ** 2,
            DRA.maxStackHeight: 2,
            DRA.status: lambda i: "PASS" if i[0] > 0 else "REJECT",
            DRA.passed: lambda i: i[0] > 0,
            DRA.rejected: lambda i: i[0] == 0,
            DRA.noError: True,
        },
    },
    swap: {
        "inputs": [(1, 2), (1, "two"), ("one", 2), ("one", "two")],
        "assertions": {
            # DRA.cost: 27,
            # DRA.lastLog: lightly_encode_output(1337, logs=True),
            DRA.finalScratch: lambda args: {
                0: 3,
                1: 4,
                2: scratch_encode(args[0]),
                3: scratch_encode(args[1]),
                4: scratch_encode(args[0]),
            },
            DRA.stackTop: 1337,
            DRA.maxStackHeight: 2,
            DRA.status: "PASS",
            DRA.passed: True,
            DRA.rejected: False,
            DRA.noError: True,
        },
    },
    string_mult: {
        "inputs": [("xyzw", i) for i in range(100)],
        "assertions": {
            # DRA.cost: lambda args: 30 + 15 * args[1],
            # DRA.lastLog: lambda args: lightly_encode_output(args[0] * args[1]) if args[1] else None,
            DRA.finalScratch: lambda args: (
                {
                    0: len(args[0]),
                    1: args[1],
                    2: args[1] + 1,
                    3: scratch_encode(args[0]),
                    4: scratch_encode(args[0] * args[1]),
                }
                if args[1]
                else {
                    0: len(args[0]),
                    2: args[1] + 1,
                    3: scratch_encode(args[0]),
                }
            ),
            DRA.stackTop: lambda args: len(args[0] * args[1]),
            DRA.maxStackHeight: lambda args: 3 if args[1] else 2,
            DRA.status: lambda args: "PASS" if args[1] else "REJECT",
            DRA.passed: lambda args: bool(args[1]),
            DRA.rejected: lambda args: not bool(args[1]),
            DRA.noError: True,
        },
    },
    oldfac: {
        "inputs": [(i,) for i in range(25)],
        "assertions": {
            # DRA.cost: lambda args, actual: actual - 40 <= 17 * args[0] <= actual + 40,
            # DRA.lastLog: lambda args, actual: (actual is None) or (int(actual, base=16) == fac_with_overflow(args[0])),
            DRA.finalScratch: lambda args: ({0: min(args[0], 21)} if args[0] else {}),
            DRA.stackTop: lambda args: fac_with_overflow(args[0]),
            DRA.maxStackHeight: lambda args: max(2, 2 * args[0]),
            DRA.status: lambda args: "PASS" if args[0] < 21 else "REJECT",
            DRA.passed: lambda args: args[0] < 21,
            DRA.rejected: lambda args: args[0] >= 21,
            DRA.noError: lambda args, actual: (
                actual is True
                if args[0] < 21
                else "logic 0 failed at line 21: * overflowed" in actual
            ),
        },
    },
    slow_fibonacci: {
        "inputs": [(i,) for i in range(18)],
        "assertions": {
            # DRA.cost: fib_cost,
            # DRA.lastLog: fib_last_log,
            # by returning True for n >= 15, we're declaring that we don't care about the scratchvar's for such cases:
            DRA.finalScratch: lambda args, actual: (
                actual == {0: args[0]}
                if 0 < args[0] < 15
                else (True if args[0] else actual == {})
            ),
            DRA.stackTop: lambda args, actual: (
                actual == fib(args[0]) if args[0] < 15 else True
            ),
            DRA.maxStackHeight: lambda args, actual: (
                actual == max(2, 2 * args[0]) if args[0] < 15 else True
            ),
            DRA.status: lambda args: "PASS" if 0 < args[0] < 15 else "REJECT",
            DRA.passed: lambda args: 0 < args[0] < 15,
            DRA.rejected: lambda args: not (0 < args[0] < 15),
            DRA.noError: lambda args, actual: (
                actual is True
                if args[0] < 15
                else "dynamic cost budget exceeded" in actual
            ),
        },
    },
}


def wrap_compile_and_save(subr, mode, version, assemble_constants, case_name):
    is_app = mode == Mode.Application

    # 1. PyTeal program Expr generation
    approval = e2e_pyteal(subr, mode)

    # 2. TEAL generation
    path = Path.cwd() / "tests" / "teal"
    teal = compileTeal(
        approval(), mode, version=version, assembleConstants=assemble_constants
    )
    filebase = f'{"app" if is_app else "lsig"}_{case_name}'
    tealpath = path / f"{filebase}.teal"
    with open(tealpath, "w") as f:
        f.write(teal)

    print(
        f"""subroutine {case_name}@{mode} generated TEAL. 
saved to {tealpath}:
-------
{teal}
-------"""
    )

    return teal, is_app, path, filebase


def semantic_test_runner(
    subr: SubroutineFnWrapper,
    mode: Mode,
    scenario: Dict[DRA, dict],
    version: int,
    assemble_constants: bool = True,
):
    case_name = subr.name()
    print(f"semantic e2e test of {case_name} with mode {mode}")

    # 0. Validations
    assert isinstance(subr, SubroutineFnWrapper), f"unexpected subr type {type(subr)}"
    assert isinstance(mode, Mode)

    teal, is_app, path, filebase = wrap_compile_and_save(
        subr, mode, version, assemble_constants, case_name
    )

    if not SEMANTIC_TESTING:
        print(
            "Exiting early without conducting end-to-end dry run testing. Sayonara!!!!!"
        )
        return

    inputs, assertions = get_blackbox_scenario_components(scenario, mode)

    # Fail fast in case algod is not configured:
    algod = algod_with_assertion()

    # 3. Build the Dryrun requests:
    drbuilder = (
        DryRunHelper.singleton_app_request
        if is_app
        else DryRunHelper.singleton_logicsig_request
    )
    dryrun_reqs = list(map(lambda a: drbuilder(teal, lightly_encode_args(a)), inputs))

    # 3. Run the requests to obtain sequence of Dryrun resonses:
    dryrun_resps = list(map(algod.dryrun, dryrun_reqs))

    # 4. Generate statistical report of all the runs:
    csvpath = path / f"{filebase}.csv"
    with open(csvpath, "w") as f:
        f.write(csv_from_dryruns(inputs, dryrun_resps))

    print(f"Saved Dry Run CSV report to {csvpath}")

    # 5. Sequential assertions (if provided any)
    for i, type_n_assertion in enumerate(assertions.items()):
        assert_type, assertion = type_n_assertion

        if SKIP_SCRATCH_ASSERTIONS and assert_type == DRA.finalScratch:
            print("skipping scratch assertions because unstable slots produced")
            continue

        assert mode_has_assertion(
            mode, assert_type
        ), f"assert_type {assert_type} is not applicable for {mode}. Please REMOVE of MODIFY"

        assertion = SequenceAssertion(
            assertion, name=f"{case_name}[{i}]@{mode}-{assert_type}"
        )
        print(
            f"{i+1}. Semantic assertion for {case_name}-{mode}: {assert_type} <<{assertion}>>"
        )
        dryrun_assert(inputs, dryrun_resps, assert_type, assertion)


@pytest.mark.skipif(not STABLE_SLOT_GENERATION, reason="cf. #199")
def test_stable_teal_generation():
    """
    Expecting this to become a flaky test very soon, and I'll turn it off at that point, happy
    knowing that can pin down an example of flakiness - Zeph 3/17/2021
    """
    if not STABLE_SLOT_GENERATION:
        print("skipping because slot generation isn't stable")
        return

    for subr, mode in product(
        [exp, square_byref, square, swap, string_mult, oldfac, slow_fibonacci],
        [Mode.Application, Mode.Signature],
    ):
        case_name = subr.name()
        print(f"stable TEAL generation test for {case_name} in mode {mode}")

        _, _, path, filebase = wrap_compile_and_save(subr, mode, 6, True, case_name)
        path2actual = path / f"{filebase}.teal"
        path2expected = path / f"{filebase}_expected.teal"
        assert_teal_as_expected(path2actual, path2expected)


@pytest.mark.parametrize("subr_n_scenario", APP_SCENARIOS.items())
def test_e2e_subroutines_as_apps(
    subr_n_scenario: Tuple[SubroutineFnWrapper, Dict[DRA, dict]]
):
    subr, scenario = subr_n_scenario
    semantic_test_runner(subr, Mode.Application, scenario, 6)


@pytest.mark.parametrize("subr_n_scenario", LOGICSIG_SCENARIOS.items())
def test_e2e_subroutines_as_logic_sigs(
    subr_n_scenario: Tuple[SubroutineFnWrapper, Dict[DRA, dict]]
):
    subr, scenario = subr_n_scenario
    semantic_test_runner(subr, Mode.Signature, scenario, 6)
