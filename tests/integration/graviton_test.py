from itertools import product
from pathlib import Path
from typing import Any, Dict

import pytest

from pyteal import (
    Bytes,
    Concat,
    For,
    If,
    Int,
    Mode,
    ScratchVar,
    Seq,
    Subroutine,
    SubroutineFnWrapper,
    TealType,
    compileTeal,
)

from tests.compile_asserts import assert_teal_as_expected
from utils.blackbox import (
    Blackbox,
    BlackboxWrapper,
    algod_with_assertion,
    blackbox_pyteal,
    mode_to_execution_mode,
)

from graviton.blackbox import (
    DryRunProperty as DRProp,
    DryRunEncoder as Encoder,
    DryRunExecutor,
    DryRunInspector,
    mode_has_property,
)

from graviton.invariant import Invariant

# TODO: remove these skips after the following issue has been fixed https://github.com/algorand/pyteal/issues/199
STABLE_SLOT_GENERATION = False
SKIP_SCRATCH_ASSERTIONS = not STABLE_SLOT_GENERATION

# ---- Helper ---- #


def wrap_compile_and_save(subr, mode, version, assemble_constants, case_name):
    is_app = mode == Mode.Application

    # 1. PyTeal program Expr generation
    approval = blackbox_pyteal(subr, mode)

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


# ---- Subroutines for Blackbox Testing ---- #


@Blackbox(input_types=[])
@Subroutine(TealType.uint64)
def exp():
    return Int(2) ** Int(10)


@Blackbox(input_types=[TealType.uint64])
@Subroutine(TealType.none)
def square_byref(x: ScratchVar):
    return x.store(x.load() * x.load())


@Blackbox(input_types=[TealType.uint64])
@Subroutine(TealType.uint64)
def square(x):
    return x ** Int(2)


@Blackbox(input_types=[TealType.anytype, TealType.anytype])
@Subroutine(TealType.none)
def swap(x: ScratchVar, y: ScratchVar):
    z = ScratchVar(TealType.anytype)
    return Seq(
        z.store(x.load()),
        x.store(y.load()),
        y.store(z.load()),
    )


@Blackbox(input_types=[TealType.bytes, TealType.uint64])
@Subroutine(TealType.bytes)
def string_mult(s: ScratchVar, n):
    i = ScratchVar(TealType.uint64)
    tmp = ScratchVar(TealType.bytes)
    start = Seq(i.store(Int(1)), tmp.store(s.load()), s.store(Bytes("")))
    step = i.store(i.load() + Int(1))
    return Seq(
        For(start, i.load() <= n, step).Do(s.store(Concat(s.load(), tmp.load()))),
        s.load(),
    )


@Blackbox(input_types=[TealType.uint64])
@Subroutine(TealType.uint64)
def oldfac(n):
    return If(n < Int(2)).Then(Int(1)).Else(n * oldfac(n - Int(1)))


@Blackbox(input_types=[TealType.uint64])
@Subroutine(TealType.uint64)
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


# ---- Blackbox pure unit tests (Skipping for now due to flakiness) ---- #


@pytest.mark.skipif(not STABLE_SLOT_GENERATION, reason="cf. #199")
@pytest.mark.parametrize(
    "subr, mode",
    product(
        [exp, square_byref, square, swap, string_mult, oldfac, slow_fibonacci],
        [Mode.Application, Mode.Signature],
    ),
)
def test_stable_teal_generation(subr, mode):
    """
    TODO: here's an example of issue #199 at play - need to run a dynamic version of `git bisect`
    to figure out what is driving this
    """
    case_name = subr.name()
    print(f"stable TEAL generation test for {case_name} in mode {mode}")

    _, _, path, filebase = wrap_compile_and_save(subr, mode, 6, True, case_name)
    path2actual = path / f"{filebase}.teal"
    path2expected = path / f"{filebase}_expected.teal"
    assert_teal_as_expected(path2actual, path2expected)


APP_SCENARIOS = {
    exp: {
        "inputs": [()],
        # since only a single input, just assert a constant in each case
        "assertions": {
            DRProp.cost: 11,
            # int assertions on log outputs need encoding to varuint-hex:
            DRProp.lastLog: Encoder.hex(2**10),
            # dicts have a special meaning as assertions. So in the case of "finalScratch"
            # which is supposed to _ALSO_ output a dict, we need to use a lambda as a work-around
            DRProp.finalScratch: lambda _: {0: 1024},
            DRProp.stackTop: 1024,
            DRProp.maxStackHeight: 2,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.errorMessage: None,
        },
    },
    square_byref: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRProp.cost: lambda _, actual: 20 < actual < 22,
            DRProp.lastLog: Encoder.hex(1337),
            # due to dry-run artifact of not reporting 0-valued scratchvars,
            # we have a special case for n=0:
            DRProp.finalScratch: lambda args, actual: (
                {1, 1337, (args[0] ** 2 if args[0] else 1)}
            ).issubset(set(actual.values())),
            DRProp.stackTop: 1337,
            DRProp.maxStackHeight: 3,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.errorMessage: None,
        },
    },
    square: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            DRProp.cost: 14,
            DRProp.lastLog: {
                # since execution REJECTS for 0, expect last log for this case to be None
                (i,): Encoder.hex(i * i) if i else None
                for i in range(100)
            },
            DRProp.finalScratch: lambda args: (
                {0: args[0] ** 2, 1: args[0]} if args[0] else {}
            ),
            DRProp.stackTop: lambda args: args[0] ** 2,
            DRProp.maxStackHeight: 2,
            DRProp.status: lambda i: "PASS" if i[0] > 0 else "REJECT",
            DRProp.passed: lambda i: i[0] > 0,
            DRProp.rejected: lambda i: i[0] == 0,
            DRProp.errorMessage: None,
        },
    },
    swap: {
        "inputs": [(1, 2), (1, "two"), ("one", 2), ("one", "two")],
        "assertions": {
            DRProp.cost: 27,
            DRProp.lastLog: Encoder.hex(1337),
            DRProp.finalScratch: lambda args: {
                0: 1337,
                1: Encoder.hex0x(args[1]),
                2: Encoder.hex0x(args[0]),
                3: 1,
                4: 2,
                5: Encoder.hex0x(args[0]),
            },
            DRProp.stackTop: 1337,
            DRProp.maxStackHeight: 2,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.errorMessage: None,
        },
    },
    string_mult: {
        "inputs": [("xyzw", i) for i in range(100)],
        "assertions": {
            DRProp.cost: lambda args: 30 + 15 * args[1],
            DRProp.lastLog: (
                lambda args: Encoder.hex(args[0] * args[1]) if args[1] else None
            ),
            # due to dryrun 0-scratchvar artifact, special case for i == 0:
            DRProp.finalScratch: lambda args: (
                {
                    0: Encoder.hex0x(args[0] * args[1]),
                    1: Encoder.hex0x(args[0] * args[1]),
                    2: 1,
                    3: args[1],
                    4: args[1] + 1,
                    5: Encoder.hex0x(args[0]),
                }
                if args[1]
                else {
                    2: 1,
                    4: args[1] + 1,
                    5: Encoder.hex0x(args[0]),
                }
            ),
            DRProp.stackTop: lambda args: len(args[0] * args[1]),
            DRProp.maxStackHeight: lambda args: 3 if args[1] else 2,
            DRProp.status: lambda args: ("PASS" if 0 < args[1] < 45 else "REJECT"),
            DRProp.passed: lambda args: 0 < args[1] < 45,
            DRProp.rejected: lambda args: 0 >= args[1] or args[1] >= 45,
            DRProp.errorMessage: None,
        },
    },
    oldfac: {
        "inputs": [(i,) for i in range(25)],
        "assertions": {
            DRProp.cost: lambda args, actual: (
                actual - 40 <= 17 * args[0] <= actual + 40
            ),
            DRProp.lastLog: lambda args: (
                Encoder.hex(fac_with_overflow(args[0])) if args[0] < 21 else None
            ),
            DRProp.finalScratch: lambda args: (
                {1: args[0], 0: fac_with_overflow(args[0])}
                if 0 < args[0] < 21
                else (
                    {1: min(21, args[0])}
                    if args[0]
                    else {0: fac_with_overflow(args[0])}
                )
            ),
            DRProp.stackTop: lambda args: fac_with_overflow(args[0]),
            DRProp.maxStackHeight: lambda args: max(2, 2 * args[0]),
            DRProp.status: lambda args: "PASS" if args[0] < 21 else "REJECT",
            DRProp.passed: lambda args: args[0] < 21,
            DRProp.rejected: lambda args: args[0] >= 21,
            DRProp.errorMessage: lambda args, actual: (
                actual is None if args[0] < 21 else "overflowed" in actual
            ),
        },
    },
    slow_fibonacci: {
        "inputs": [(i,) for i in range(18)],
        "assertions": {
            DRProp.cost: lambda args: (fib_cost(args) if args[0] < 17 else 70_000),
            DRProp.lastLog: lambda args: (
                Encoder.hex(fib(args[0])) if 0 < args[0] < 17 else None
            ),
            DRProp.finalScratch: lambda args, actual: (
                actual == {1: args[0], 0: fib(args[0])}
                if 0 < args[0] < 17
                else (True if args[0] >= 17 else actual == {})
            ),
            # we declare to "not care" about the top of the stack for n >= 17
            DRProp.stackTop: lambda args, actual: (
                actual == fib(args[0]) if args[0] < 17 else True
            ),
            # similarly, we don't care about max stack height for n >= 17
            DRProp.maxStackHeight: lambda args, actual: (
                actual == max(2, 2 * args[0]) if args[0] < 17 else True
            ),
            DRProp.status: lambda args: "PASS" if 0 < args[0] < 8 else "REJECT",
            DRProp.passed: lambda args: 0 < args[0] < 8,
            DRProp.rejected: lambda args: 0 >= args[0] or args[0] >= 8,
            DRProp.errorMessage: lambda args, actual: (
                actual is None
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
            # DRProp.cost: 11,
            # DRProp.lastLog: Encoder.hex(2 ** 10),
            DRProp.finalScratch: lambda _: {},
            DRProp.stackTop: 1024,
            DRProp.maxStackHeight: 2,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.errorMessage: None,
        },
    },
    square_byref: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            # DRProp.cost: lambda _, actual: 20 < actual < 22,
            # DRProp.lastLog: Encoder.hex(1337),
            # due to dry-run artifact of not reporting 0-valued scratchvars,
            # we have a special case for n=0:
            DRProp.finalScratch: lambda args: (
                {0: 1, 1: args[0] ** 2} if args[0] else {0: 1}
            ),
            DRProp.stackTop: 1337,
            DRProp.maxStackHeight: 3,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.errorMessage: None,
        },
    },
    square: {
        "inputs": [(i,) for i in range(100)],
        "assertions": {
            # DRProp.cost: 14,
            # DRProp.lastLog: {(i,): Encoder.hex(i * i) if i else None for i in range(100)},
            DRProp.finalScratch: lambda args: ({0: args[0]} if args[0] else {}),
            DRProp.stackTop: lambda args: args[0] ** 2,
            DRProp.maxStackHeight: 2,
            DRProp.status: lambda i: "PASS" if i[0] > 0 else "REJECT",
            DRProp.passed: lambda i: i[0] > 0,
            DRProp.rejected: lambda i: i[0] == 0,
            DRProp.errorMessage: None,
        },
    },
    swap: {
        "inputs": [(1, 2), (1, "two"), ("one", 2), ("one", "two")],
        "assertions": {
            # DRProp.cost: 27,
            # DRProp.lastLog: Encoder.hex(1337),
            DRProp.finalScratch: lambda args: {
                0: 3,
                1: 4,
                2: Encoder.hex0x(args[0]),
                3: Encoder.hex0x(args[1]),
                4: Encoder.hex0x(args[0]),
            },
            DRProp.stackTop: 1337,
            DRProp.maxStackHeight: 2,
            DRProp.status: "PASS",
            DRProp.passed: True,
            DRProp.rejected: False,
            DRProp.errorMessage: None,
        },
    },
    string_mult: {
        "inputs": [("xyzw", i) for i in range(100)],
        "assertions": {
            # DRProp.cost: lambda args: 30 + 15 * args[1],
            # DRProp.lastLog: lambda args: Encoder.hex(args[0] * args[1]) if args[1] else None,
            DRProp.finalScratch: lambda args: (
                {
                    0: len(args[0]),
                    1: args[1],
                    2: args[1] + 1,
                    3: Encoder.hex0x(args[0]),
                    4: Encoder.hex0x(args[0] * args[1]),
                }
                if args[1]
                else {
                    0: len(args[0]),
                    2: args[1] + 1,
                    3: Encoder.hex0x(args[0]),
                }
            ),
            DRProp.stackTop: lambda args: len(args[0] * args[1]),
            DRProp.maxStackHeight: lambda args: 3 if args[1] else 2,
            DRProp.status: lambda args: "PASS" if args[1] else "REJECT",
            DRProp.passed: lambda args: bool(args[1]),
            DRProp.rejected: lambda args: not bool(args[1]),
            DRProp.errorMessage: None,
        },
    },
    oldfac: {
        "inputs": [(i,) for i in range(25)],
        "assertions": {
            # DRProp.cost: lambda args, actual: actual - 40 <= 17 * args[0] <= actual + 40,
            # DRProp.lastLog: lambda args, actual: (actual is None) or (int(actual, base=16) == fac_with_overflow(args[0])),
            DRProp.finalScratch: lambda args: (
                {0: min(args[0], 21)} if args[0] else {}
            ),
            DRProp.stackTop: lambda args: fac_with_overflow(args[0]),
            DRProp.maxStackHeight: lambda args: max(2, 2 * args[0]),
            DRProp.status: lambda args: "PASS" if args[0] < 21 else "REJECT",
            DRProp.passed: lambda args: args[0] < 21,
            DRProp.rejected: lambda args: args[0] >= 21,
            DRProp.errorMessage: lambda args, actual: (
                actual is None
                if args[0] < 21
                else "logic 0 failed at line 21: * overflowed" in actual
            ),
        },
    },
    slow_fibonacci: {
        "inputs": [(i,) for i in range(18)],
        "assertions": {
            # DRProp.cost: fib_cost,
            # DRProp.lastLog: fib_last_log,
            # by returning True for n >= 15, we're declaring that we don't care about the scratchvar's for such cases:
            DRProp.finalScratch: lambda args, actual: (
                actual == {0: args[0]}
                if 0 < args[0] < 15
                else (True if args[0] else actual == {})
            ),
            DRProp.stackTop: lambda args, actual: (
                actual == fib(args[0]) if args[0] < 15 else True
            ),
            DRProp.maxStackHeight: lambda args, actual: (
                actual == max(2, 2 * args[0]) if args[0] < 15 else True
            ),
            DRProp.status: lambda args: "PASS" if 0 < args[0] < 15 else "REJECT",
            DRProp.passed: lambda args: 0 < args[0] < 15,
            DRProp.rejected: lambda args: not (0 < args[0] < 15),
            DRProp.errorMessage: lambda args, actual: (
                actual is None
                if args[0] < 15
                else "dynamic cost budget exceeded" in actual
            ),
        },
    },
}


def blackbox_test_runner(
    subr: SubroutineFnWrapper,
    mode: Mode,
    scenario: Dict[str, Any],
    version: int,
    assemble_constants: bool = True,
):
    case_name = subr.name()
    print(f"blackbox test of {case_name} with mode {mode}")
    exec_mode = mode_to_execution_mode(mode)

    # 0. Validations
    assert isinstance(subr, BlackboxWrapper), f"unexpected subr type {type(subr)}"
    assert isinstance(mode, Mode)

    # 1. Compile to TEAL
    teal, _, path, filebase = wrap_compile_and_save(
        subr, mode, version, assemble_constants, case_name
    )

    # Fail fast in case algod is not configured:
    algod = algod_with_assertion()

    # 2. validate dry run scenarios:
    inputs, predicates = Invariant.inputs_and_invariants(
        scenario, exec_mode, raw_predicates=True
    )

    # 3. execute dry run sequence:
    execute = DryRunExecutor.execute_one_dryrun
    inspectors = list(map(lambda a: execute(algod, teal, a, exec_mode), inputs))

    # 4. Statistical report:
    csvpath = path / f"{filebase}.csv"
    with open(csvpath, "w") as f:
        f.write(DryRunInspector.csv_report(inputs, inspectors))

    print(f"Saved Dry Run CSV report to {csvpath}")

    # 5. Sequential assertions (if provided any)
    for i, type_n_assertion in enumerate(predicates.items()):
        dr_prop, predicate = type_n_assertion

        if SKIP_SCRATCH_ASSERTIONS and dr_prop == DRProp.finalScratch:
            print("skipping scratch assertions because unstable slots produced")
            continue

        assert mode_has_property(exec_mode, dr_prop)

        invariant = Invariant(predicate, name=f"{case_name}[{i}]@{mode}-{dr_prop}")
        print(f"{i+1}. Assertion for {case_name}-{mode}: {dr_prop} <<{predicate}>>")
        invariant.validates(dr_prop, inputs, inspectors)


# ---- Graviton / Blackbox tests ---- #


@pytest.mark.parametrize("subr, scenario", APP_SCENARIOS.items())
def test_blackbox_subroutines_as_apps(
    subr: SubroutineFnWrapper,
    scenario: Dict[str, Any],
):
    blackbox_test_runner(subr, Mode.Application, scenario, 6)


@pytest.mark.parametrize("subr, scenario", LOGICSIG_SCENARIOS.items())
def test_blackbox_subroutines_as_logic_sigs(
    subr: SubroutineFnWrapper,
    scenario: Dict[str, Any],
):
    blackbox_test_runner(subr, Mode.Signature, scenario, 6)
