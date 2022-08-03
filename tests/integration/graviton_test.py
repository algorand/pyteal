from itertools import product
from pathlib import Path
from typing import Any, Dict

import pytest

import pyteal as pt

from tests.compile_asserts import assert_teal_as_expected
from tests.blackbox import (
    Blackbox,
    BlackboxWrapper,
    algod_with_assertion,
    mode_to_execution_mode,
    PyTealDryRunExecutor,
)

from graviton.blackbox import (
    DryRunProperty as DRProp,
    DryRunEncoder as Encoder,
    DryRunExecutor,
    DryRunInspector,
    mode_has_property,
)

from graviton.invariant import Invariant

PATH = Path.cwd() / "tests" / "integration"
FIXTURES = PATH / "teal"
GENERATED = PATH / "generated"

# TODO: remove these skips after the following issue has been fixed https://github.com/algorand/pyteal/issues/199
STABLE_SLOT_GENERATION = False
SKIP_SCRATCH_ASSERTIONS = not STABLE_SLOT_GENERATION

# ---- Helper ---- #


def wrap_compile_and_save(
    subr, mode, version, assemble_constants, test_name, case_name
):
    is_app = mode == pt.Mode.Application

    teal = PyTealDryRunExecutor(subr, mode).compile(version, assemble_constants)
    tealfile = f'{"app" if is_app else "lsig"}_{case_name}.teal'

    tealdir = GENERATED / test_name
    tealdir.mkdir(parents=True, exist_ok=True)
    tealpath = tealdir / tealfile
    with open(tealpath, "w") as f:
        f.write(teal)

    print(
        f"""Subroutine {case_name}@{mode} generated TEAL.
saved to {tealpath}:
-------
{teal}
-------"""
    )

    return teal, is_app, tealfile


# ---- Subroutines for Blackbox Testing ---- #


@Blackbox(input_types=[])
@pt.Subroutine(pt.TealType.uint64)
def exp():
    return pt.Int(2) ** pt.Int(10)


@Blackbox(input_types=[pt.TealType.uint64])
@pt.Subroutine(pt.TealType.none)
def square_byref(x: pt.ScratchVar):
    return x.store(x.load() * x.load())


@Blackbox(input_types=[pt.TealType.uint64])
@pt.Subroutine(pt.TealType.uint64)
def square(x):
    return x ** pt.Int(2)


@Blackbox(input_types=[pt.TealType.anytype, pt.TealType.anytype])
@pt.Subroutine(pt.TealType.none)
def swap(x: pt.ScratchVar, y: pt.ScratchVar):
    z = pt.ScratchVar(pt.TealType.anytype)
    return pt.Seq(
        z.store(x.load()),
        x.store(y.load()),
        y.store(z.load()),
    )


@Blackbox(input_types=[pt.TealType.bytes, pt.TealType.uint64])
@pt.Subroutine(pt.TealType.bytes)
def string_mult(s: pt.ScratchVar, n):
    i = pt.ScratchVar(pt.TealType.uint64)
    tmp = pt.ScratchVar(pt.TealType.bytes)
    start = pt.Seq(i.store(pt.Int(1)), tmp.store(s.load()), s.store(pt.Bytes("")))
    step = i.store(i.load() + pt.Int(1))
    return pt.Seq(
        pt.For(start, i.load() <= n, step).Do(s.store(pt.Concat(s.load(), tmp.load()))),
        s.load(),
    )


@Blackbox(input_types=[pt.TealType.uint64])
@pt.Subroutine(pt.TealType.uint64)
def oldfac(n):
    return pt.If(n < pt.Int(2)).Then(pt.Int(1)).Else(n * oldfac(n - pt.Int(1)))


@Blackbox(input_types=[pt.TealType.uint64])
@pt.Subroutine(pt.TealType.uint64)
def slow_fibonacci(n):
    return (
        pt.If(n <= pt.Int(1))
        .Then(n)
        .Else(slow_fibonacci(n - pt.Int(2)) + slow_fibonacci(n - pt.Int(1)))
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
        [pt.Mode.Application, pt.Mode.Signature],
    ),
)
def test_stable_teal_generation(subr, mode):
    """
    TODO: here's an example of issue #199 at play - need to run a dynamic version of `git bisect`
    to figure out what is driving this
    """
    case_name = subr.name()
    print(f"stable TEAL generation test for {case_name} in mode {mode}")

    _, _, tealfile = wrap_compile_and_save(subr, mode, 6, True, "stability", case_name)
    path2actual = GENERATED / "stability" / tealfile
    path2expected = FIXTURES / "stability" / tealfile
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
    subr: pt.SubroutineFnWrapper,
    mode: pt.Mode,
    scenario: Dict[str, Any],
    version: int,
    assemble_constants: bool = True,
):
    case_name = subr.name()
    print(f"blackbox test of {case_name} with mode {mode}")
    exec_mode = mode_to_execution_mode(mode)

    # 0. Validations
    assert isinstance(subr, BlackboxWrapper), f"unexpected subr type {type(subr)}"
    assert isinstance(mode, pt.Mode)

    # 1. Compile to TEAL
    teal, _, tealfile = wrap_compile_and_save(
        subr, mode, version, assemble_constants, "blackbox", case_name
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
    csvpath = GENERATED / "blackbox" / f"{tealfile}.csv"
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
    subr: pt.SubroutineFnWrapper,
    scenario: Dict[str, Any],
):
    blackbox_test_runner(subr, pt.Mode.Application, scenario, 6)


@pytest.mark.parametrize("subr, scenario", LOGICSIG_SCENARIOS.items())
def test_blackbox_subroutines_as_logic_sigs(
    subr: pt.SubroutineFnWrapper,
    scenario: Dict[str, Any],
):
    blackbox_test_runner(subr, pt.Mode.Signature, scenario, 6)


def blackbox_pyteal_example1():
    # Example 1: Using blackbox_pyteal for a simple test of both an app and logic sig:
    from graviton.blackbox import DryRunEncoder

    from pyteal import Int, Mode, Subroutine, TealType
    from tests.blackbox import Blackbox

    @Blackbox(input_types=[TealType.uint64])
    @Subroutine(TealType.uint64)
    def square(x):
        return x ** Int(2)

    # provide args for evaluation (will compute x^2)
    x = 9
    args = [x]

    # evaluate the programs
    app_result = PyTealDryRunExecutor(square, Mode.Application).dryrun(args)
    lsig_result = PyTealDryRunExecutor(square, Mode.Signature).dryrun(args)

    # check to see that x^2 is at the top of the stack as expected
    assert app_result.stack_top() == x**2, app_result.report(
        args, "stack_top() gave unexpected results for app"
    )
    assert lsig_result.stack_top() == x**2, lsig_result.report(
        args, "stack_top() gave unexpected results for lsig"
    )

    # check to see that itob of x^2 has been logged (only for the app case)
    assert app_result.last_log() == DryRunEncoder.hex(x**2), app_result.report(
        args, "last_log() gave unexpected results from app"
    )


def blackbox_pyteal_example2():
    # Example 2: Using blackbox_pyteal to make 400 assertions and generate a CSV report with 400 dryrun rows
    from itertools import product
    import math
    from pathlib import Path
    import random

    from graviton.blackbox import DryRunInspector

    from pyteal import (
        For,
        If,
        Int,
        Mod,
        Mode,
        ScratchVar,
        Seq,
        Subroutine,
        TealType,
    )

    from tests.blackbox import Blackbox

    # GCD via the Euclidean Algorithm (iterative version):
    @Blackbox(input_types=[TealType.uint64, TealType.uint64])
    @Subroutine(TealType.uint64)
    def euclid(x, y):
        a = ScratchVar(TealType.uint64)
        b = ScratchVar(TealType.uint64)
        tmp = ScratchVar(TealType.uint64)
        start = If(x < y, Seq(a.store(y), b.store(x)), Seq(a.store(x), b.store(y)))
        cond = b.load() > Int(0)
        step = Seq(
            tmp.store(b.load()), b.store(Mod(a.load(), b.load())), a.store(tmp.load())
        )
        return Seq(For(start, cond, step).Do(Seq()), a.load())

    # generate a report with 400 = 20*20 dry run rows:
    N = 20
    inputs = list(
        product(
            tuple(random.randint(0, 1000) for _ in range(N)),
            tuple(random.randint(0, 1000) for _ in range(N)),
        )
    )

    # assert that each result is that same as what Python's math.gcd() computes
    inspectors = PyTealDryRunExecutor(euclid, Mode.Application).dryrun_on_sequence(
        inputs
    )
    for i, result in enumerate(inspectors):
        args = inputs[i]
        assert result.stack_top() == math.gcd(*args), result.report(
            args, f"failed for {args}"
        )

    # save the CSV to ...current working directory.../euclid.csv
    euclid_csv = DryRunInspector.csv_report(inputs, inspectors)
    with open(Path.cwd() / "euclid.csv", "w") as f:
        f.write(euclid_csv)


def blackbox_pyteal_example3():
    # Example 3: declarative Test Driven Development approach through Invariant's
    from itertools import product
    import math
    import random

    from graviton.blackbox import (
        DryRunEncoder,
        DryRunProperty as DRProp,
    )
    from graviton.invariant import Invariant

    from pyteal import If, Int, Mod, Mode, Subroutine, TealType

    from tests.blackbox import Blackbox

    # avoid flaky tests just in case I was wrong about the stack height invariant...
    random.seed(42)

    # helper that will be used for scratch-slots invariant:
    def is_subdict(x, y):
        return all(k in y and x[k] == y[k] for k in x)

    predicates = {
        # the program's log should be the hex encoding of Python's math.gcd:
        DRProp.lastLog: lambda args: (
            DryRunEncoder.hex(math.gcd(*args)) if math.gcd(*args) else None
        ),
        # the program's scratch should contain math.gcd() at slot 0:
        DRProp.finalScratch: lambda args, actual: is_subdict(
            {0: math.gcd(*args)}, actual
        ),
        # the top of the stack should be math.gcd():
        DRProp.stackTop: lambda args: math.gcd(*args),
        # Making the rather weak assertion that the max stack height is between 2 and 3*log2(max(args)):
        DRProp.maxStackHeight: (
            lambda args, actual: 2
            <= actual
            <= 3 * math.ceil(math.log2(max(args + (1,))))
        ),
        # the program PASS'es exactly for non-0 math.gcd (3 variants):
        DRProp.status: lambda args: "PASS" if math.gcd(*args) else "REJECT",
        DRProp.passed: lambda args: bool(math.gcd(*args)),
        DRProp.rejected: lambda args: not bool(math.gcd(*args)),
        # the program never errors:
        DRProp.errorMessage: None,
    }

    # Define a scenario 400 random pairs (x,y) as inputs:
    N = 20
    inputs = list(
        product(
            tuple(random.randint(0, 1000) for _ in range(N)),
            tuple(random.randint(0, 1000) for _ in range(N)),
        )
    )

    # GCD via the Euclidean Algorithm (recursive version):
    @Blackbox(input_types=[TealType.uint64, TealType.uint64])
    @Subroutine(TealType.uint64)
    def euclid(x, y):
        return (
            If(x < y)
            .Then(euclid(y, x))
            .Else(If(y == Int(0)).Then(x).Else(euclid(y, Mod(x, y))))
        )

    # Execute on the input sequence to get a dry-run inspectors:
    inspectors = PyTealDryRunExecutor(euclid, Mode.Application).dryrun_on_sequence(
        inputs
    )

    # Assert that each invariant holds on the sequences of inputs and dry-runs:
    for property, predicate in predicates.items():
        Invariant(predicate).validates(property, inputs, inspectors)


def blackbox_pyteal_example4():
    # Example 4: Using PyTealDryRunExecutor to debug an ABIReturnSubroutine with an app, logic sig and csv report
    from pathlib import Path
    import random

    from graviton.blackbox import DryRunInspector

    from pyteal import (
        abi,
        ABIReturnSubroutine,
        Expr,
        For,
        Int,
        Mode,
        ScratchVar,
        Seq,
        TealType,
    )

    from tests.blackbox import Blackbox, PyTealDryRunExecutor

    # Sum a dynamic uint64 array
    @Blackbox(input_types=[None])
    @ABIReturnSubroutine
    def abi_sum(toSum: abi.DynamicArray[abi.Uint64], *, output: abi.Uint64) -> Expr:
        i = ScratchVar(TealType.uint64)
        valueAtIndex = abi.Uint64()
        return Seq(
            output.set(0),
            For(
                i.store(Int(0)),
                i.load() < toSum.length(),
                i.store(i.load() + Int(1)),
            ).Do(
                Seq(
                    toSum[i.load()].store_into(valueAtIndex),
                    output.set(output.get() + valueAtIndex.get()),
                )
            ),
        )

    # instantiate PyTealDryRunExecutor objects for the app and lsig:
    app_pytealer = PyTealDryRunExecutor(abi_sum, Mode.Application)
    lsig_pytealer = PyTealDryRunExecutor(abi_sum, Mode.Signature)

    # generate reports with the same random inputs (fix the randomness with a seed):
    random.seed(42)

    N = 50  # the number of dry runs for each experiment
    choices = range(10_000)
    inputs = []
    for n in range(N):
        inputs.append(tuple([random.sample(choices, n)]))

    app_inspectors = app_pytealer.dryrun_on_sequence(inputs)

    lsig_inspectors = lsig_pytealer.dryrun_on_sequence(inputs)

    for i in range(N):
        args = inputs[i]

        app_inspector = app_inspectors[i]
        lsig_inspector = lsig_inspectors[i]

        def message(insp):
            return insp.report(args, f"failed for {args}", row=i)

        # the app should pass exactly when it's cost was within the 700 budget:
        assert app_inspector.passed() == (app_inspector.cost() <= 700), message(
            app_inspector
        )
        # the lsig always passes (never goes over budget):
        assert lsig_inspector.passed(), message(lsig_inspector)

        expected = sum(args[0])
        actual4app = app_inspector.last_log()
        assert expected == actual4app, message(app_inspector)

        if i > 0:
            assert expected in app_inspector.final_scratch().values(), message(
                app_inspector
            )
            assert expected in lsig_inspector.final_scratch().values(), message(
                lsig_inspector
            )

    def report(kind):
        assert kind in ("app", "lsig")
        insps = app_inspectors if kind == "app" else lsig_inspectors
        csv_report = DryRunInspector.csv_report(inputs, insps)
        with open(Path.cwd() / f"abi_sum_{kind}.csv", "w") as f:
            f.write(csv_report)

    report("app")
    report("lsig")


def blackbox_pyteal_example5():
    from graviton.blackbox import DryRunEncoder

    from pyteal import abi, Subroutine, TealType, Int, Mode
    from tests.blackbox import Blackbox

    @Blackbox([None])
    @Subroutine(TealType.uint64)
    def cubed(n: abi.Uint64):
        return n.get() ** Int(3)

    app_pytealer = PyTealDryRunExecutor(cubed, Mode.Application)
    lsig_pytealer = PyTealDryRunExecutor(cubed, Mode.Signature)

    inputs = [[i] for i in range(1, 11)]

    app_inspect = app_pytealer.dryrun_on_sequence(inputs)
    lsig_inspect = lsig_pytealer.dryrun_on_sequence(inputs)

    for index, inspect in enumerate(app_inspect):
        input_var = inputs[index][0]
        assert inspect.stack_top() == input_var**3, inspect.report(
            args=inputs[index], msg="stack_top() gave unexpected results from app"
        )
        assert inspect.last_log() == DryRunEncoder.hex(input_var**3), inspect.report(
            args=inputs[index], msg="last_log() gave unexpected results from app"
        )

    for index, inspect in enumerate(lsig_inspect):
        input_var = inputs[index][0]
        assert inspect.stack_top() == input_var**3, inspect.report(
            args=inputs[index], msg="stack_top() gave unexpected results from app"
        )


def blackbox_pyteal_while_continue_test():
    from tests.blackbox import Blackbox
    from pyteal import (
        Continue,
        Int,
        Mode,
        Return,
        ScratchVar,
        Seq,
        Subroutine,
        TealType,
        While,
    )

    @Blackbox(input_types=[TealType.uint64])
    @Subroutine(TealType.uint64)
    def while_continue_accumulation(n):
        i = ScratchVar(TealType.uint64)
        return Seq(
            i.store(Int(0)),
            While(i.load() < n).Do(
                Seq(
                    i.store(i.load() + Int(1)),
                    Continue(),
                )
            ),
            Return(i.load()),
        )

    for x in range(30):
        args = [x]
        lsig_result = PyTealDryRunExecutor(
            while_continue_accumulation, Mode.Signature
        ).dryrun(args)
        if x == 0:
            assert not lsig_result.passed()
        else:
            assert lsig_result.passed()

        assert lsig_result.stack_top() == x, lsig_result.report(
            args, "stack_top() gave unexpected results for lsig"
        )


def blackbox_pyteal_named_tupleness_test():
    from typing import Literal as L
    from tests.blackbox import Blackbox
    from pyteal import (
        Seq,
        abi,
        Subroutine,
        TealType,
        Return,
        And,
        Mode,
    )

    class NamedTupleExample(abi.NamedTuple):
        a: abi.Field[abi.Bool]
        b: abi.Field[abi.Address]
        c: abi.Field[abi.Tuple2[abi.Uint64, abi.Bool]]
        d: abi.Field[abi.StaticArray[abi.Byte, L[10]]]
        e: abi.Field[abi.StaticArray[abi.Bool, L[4]]]
        f: abi.Field[abi.Uint64]

    @Blackbox(input_types=[None] * 6)
    @Subroutine(TealType.uint64)
    def named_tuple_field_access(
        a_0: abi.Bool,
        a_1: abi.Address,
        a_2: abi.Tuple2[abi.Uint64, abi.Bool],
        a_3: abi.StaticArray[abi.Byte, L[10]],
        a_4: abi.StaticArray[abi.Bool, L[4]],
        a_5: abi.Uint64,
    ):
        return Seq(
            (v_tuple := NamedTupleExample()).set(a_0, a_1, a_2, a_3, a_4, a_5),
            (v_a := abi.Bool()).set(v_tuple.a),
            (v_b := abi.Address()).set(v_tuple.b),
            (v_c := abi.make(abi.Tuple2[abi.Uint64, abi.Bool])).set(v_tuple.c),
            (v_d := abi.make(abi.StaticArray[abi.Byte, L[10]])).set(v_tuple.d),
            (v_e := abi.make(abi.StaticArray[abi.Bool, L[4]])).set(v_tuple.e),
            (v_f := abi.Uint64()).set(v_tuple.f),
            Return(
                And(
                    a_0.get() == v_a.get(),
                    a_1.get() == v_b.get(),
                    a_2.encode() == v_c.encode(),
                    a_3.encode() == v_d.encode(),
                    a_4.encode() == v_e.encode(),
                    a_5.get() == v_f.get(),
                )
            ),
        )

    lsig_pytealer = PyTealDryRunExecutor(named_tuple_field_access, Mode.Signature)
    args = (False, b"1" * 32, (0, False), b"0" * 10, [True] * 4, 0)

    inspector = lsig_pytealer.dryrun(args)

    assert inspector.stack_top() == 1
    assert inspector.passed()


@pytest.mark.parametrize(
    "example",
    [
        blackbox_pyteal_example1,
        blackbox_pyteal_example2,
        blackbox_pyteal_example3,
        blackbox_pyteal_example4,
        blackbox_pyteal_example5,
        blackbox_pyteal_while_continue_test,
        blackbox_pyteal_named_tupleness_test,
    ],
)
def test_blackbox_pyteal_examples(example):
    example()
