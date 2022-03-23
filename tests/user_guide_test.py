import os
import pytest

from itertools import product
import math
from pathlib import Path
import random


from algosdk.testing.teal_blackbox import (
    DryRunEncoder,
    DryRunExecutor as Executor,
    DryRunProperty as DRProp,
    DryRunTransactionResult,
    SequenceAssertion,
)

from pyteal import *


from .compile_asserts import assert_new_v_old
from .blackbox_asserts import (
    blackbox_pyteal,
    algod_with_assertion,
    mode_to_execution_mode,
)

BLACKBOX_TESTING = os.environ.get("HAS_ALGOD") == "TRUE"


def user_guide_snippet_dynamic_scratch_var() -> Expr:
    """
    The user guide docs use the test to illustrate `DynamicScratchVar` usage.  If the test breaks, then the user guide docs must be updated along with the test.
    """

    s = ScratchVar(TealType.uint64)
    d = DynamicScratchVar(TealType.uint64)

    return Seq(
        d.set_index(s),
        s.store(Int(7)),
        d.store(d.load() + Int(3)),
        Assert(s.load() == Int(10)),
        Int(1),
    )


# RECURSIVE VERSION HAS AN INFINITE LOOP!!!!
@Subroutine(TealType.uint64, input_types=[TealType.uint64, TealType.uint64])
def buggy_euclid(x, y):
    return (
        If(x < y)
        .Then(buggy_euclid(y, x))
        .Else(If(y == Int(0)).Then(x).Else(buggy_euclid(x, Mod(y, x))))
    )


def test_blackbox_pyteal_examples():
    ##### COMPILATION #####
    # Example 1 - test both app and logic sig
    @Subroutine(TealType.uint64, input_types=[TealType.uint64])
    def square(x):
        return x ** Int(2)

    # use this function to create pyteal app and signature expression approval functions:
    approval_app = blackbox_pyteal(square, Mode.Application)
    approval_lsig = blackbox_pyteal(square, Mode.Signature)

    # compile the evaluated approvals to generate TEAL code
    app_teal = compileTeal(approval_app(), Mode.Application, version=6)
    lsig_teal = compileTeal(approval_lsig(), Mode.Signature, version=6)

    # Example 2 - Euclidean Algorithm with many inputs and a CSV report
    @Subroutine(TealType.uint64, input_types=[TealType.uint64, TealType.uint64])
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

    euclid_app = blackbox_pyteal(euclid, Mode.Application)
    euclid_app_teal = compileTeal(euclid_app(), Mode.Application, version=6)

    # Example 3: A Declarative Test Scenario
    def is_subdict(x, y):
        return all(k in y and x[k] == y[k] for k in x)

    N = 20
    scenario = {
        "inputs": list(
            product(
                tuple(random.randint(0, 1000) for _ in range(N)),
                tuple(random.randint(0, 1000) for _ in range(N)),
            )
        ),
        "assertions": {
            DRProp.lastLog: lambda args: (
                DryRunEncoder.hex(math.gcd(*args)) if math.gcd(*args) else None
            ),
            DRProp.finalScratch: lambda args, actual: is_subdict(
                {0: math.gcd(*args)}, actual
            ),
            DRProp.stackTop: lambda args: math.gcd(*args),
            DRProp.maxStackHeight: 2,
            DRProp.status: lambda args: "PASS" if math.gcd(*args) else "REJECT",
            DRProp.passed: lambda args: bool(math.gcd(*args)),
            DRProp.rejected: lambda args: not bool(math.gcd(*args)),
            DRProp.errorMessage: None,
        },
    }

    if not BLACKBOX_TESTING:
        print("exiting test without dry run execution")
        return

    ##### EXECUTION #####
    # Example 1
    # provide args for evaluation (will compute x^2)
    x = 9
    args = [x]

    # evaluate the programs
    algod = algod_with_assertion()
    app_result = Executor.dryrun_app(algod, app_teal, args)
    lsig_result = Executor.dryrun_logicsig(algod, lsig_teal, args)

    # check to see that x^2 is at the top of the stack as expected
    assert app_result.stack_top() == x ** 2, app_result.report(
        args, "stack_top() failed for app"
    )
    assert lsig_result.stack_top() == x ** 2, lsig_result.report(
        args, "stack_top() failed for lsig"
    )

    # check to see that itob of x^2 has been logged (only for the app case)
    assert app_result.last_log() == DryRunEncoder.hex(x ** 2), app_result.report(
        args, "last_log() failed for app"
    )

    # Example 2
    # generate a report with 400 = 20*20 dry run rows:
    inputs = list(
        product(
            tuple(random.randint(0, 1000) for _ in range(N)),
            tuple(random.randint(0, 1000) for _ in range(N)),
        )
    )
    euclid_results = Executor.dryrun_app_on_sequence(algod, euclid_app_teal, inputs)
    for i, result in enumerate(euclid_results):
        args = inputs[i]
        assert result.stack_top() == math.gcd(*args), result.report(
            args, f"failed for {args}"
        )
    euclid_csv = DryRunTransactionResult.csv_report(inputs, euclid_results)
    with open(Path.cwd() / "euclid.csv", "w") as f:
        f.write(euclid_csv)

    # Example 3
    exec_mode = mode_to_execution_mode(Mode.Application)
    inputs, assertions = SequenceAssertion.inputs_and_assertions(scenario, exec_mode)
    euclid_results = Executor.dryrun_app_on_sequence(algod, euclid_app_teal, inputs)
    for assert_type, predicate in assertions.items():
        assertion = SequenceAssertion(predicate, name=str(assert_type))
        assertion.dryrun_assert(inputs, euclid_results, assert_type)


@pytest.mark.parametrize("snippet", [user_guide_snippet_dynamic_scratch_var])
def test_user_guide_snippets(snippet):
    assert_new_v_old(snippet, version=6)
