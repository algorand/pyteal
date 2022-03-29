import pytest


from pyteal import *


from .compile_asserts import assert_new_v_old


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


def blackbox_pyteal_example1():
    # Example 1: Using blackbox_pyteal for a simple test of both an app and logic sig:
    from graviton.blackbox import DryRunEncoder, DryRunExecutor

    from tests.blackbox_asserts import algod_with_assertion, blackbox_pyteal

    @Subroutine(TealType.uint64, input_types=[TealType.uint64])
    def square(x):
        return x ** Int(2)

    # create pyteal app and logic sig approvals:
    approval_app = blackbox_pyteal(square, Mode.Application)
    approval_lsig = blackbox_pyteal(square, Mode.Signature)

    # compile the evaluated approvals to generate TEAL:
    app_teal = compileTeal(approval_app(), Mode.Application, version=6)
    lsig_teal = compileTeal(approval_lsig(), Mode.Signature, version=6)

    # provide args for evaluation (will compute x^2)
    x = 9
    args = [x]

    # evaluate the programs
    algod = algod_with_assertion()
    app_result = DryRunExecutor.dryrun_app(algod, app_teal, args)
    lsig_result = DryRunExecutor.dryrun_logicsig(algod, lsig_teal, args)

    # check to see that x^2 is at the top of the stack as expected
    assert app_result.stack_top() == x ** 2, app_result.report(
        args, "stack_top() gave unexpected results for app"
    )
    assert lsig_result.stack_top() == x ** 2, lsig_result.report(
        args, "stack_top() gave unexpected results for lsig"
    )

    # check to see that itob of x^2 has been logged (only for the app case)
    assert app_result.last_log() == DryRunEncoder.hex(x ** 2), app_result.report(
        args, "last_log() gave unexprected results from app"
    )


def blackbox_pyteal_example2():
    # Example 2: Using blackbox_pyteal to make 400 assertions and generate a CSV report with 400 dryrun rows
    from itertools import product
    import math
    from pathlib import Path
    import random

    from graviton.blackbox import DryRunExecutor, DryRunInspector

    from tests.blackbox_asserts import algod_with_assertion, blackbox_pyteal

    # GCD via the Euclidean Algorithm (iterative version):
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

    # create approval PyTeal and compile it to TEAL:
    euclid_app = blackbox_pyteal(euclid, Mode.Application)
    euclid_app_teal = compileTeal(euclid_app(), Mode.Application, version=6)

    # generate a report with 400 = 20*20 dry run rows:
    N = 20
    inputs = list(
        product(
            tuple(random.randint(0, 1000) for _ in range(N)),
            tuple(random.randint(0, 1000) for _ in range(N)),
        )
    )

    # execute the dry-run sequence:
    algod = algod_with_assertion()

    # assert that each result is that same as what Python's math.gcd() computes
    inspectors = DryRunExecutor.dryrun_app_on_sequence(algod, euclid_app_teal, inputs)
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

    # avoid flaky tests just in case I was wrong about the stack height invariant...
    random.seed(42)

    from graviton.blackbox import (
        DryRunEncoder,
        DryRunExecutor,
        DryRunProperty as DRProp,
    )
    from graviton.invariant import Invariant

    from tests.blackbox_asserts import (
        algod_with_assertion,
        blackbox_pyteal,
        mode_to_execution_mode,
    )

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
        # the program never erors:
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
    @Subroutine(TealType.uint64, input_types=[TealType.uint64, TealType.uint64])
    def euclid(x, y):
        return (
            If(x < y)
            .Then(euclid(y, x))
            .Else(If(y == Int(0)).Then(x).Else(euclid(y, Mod(x, y))))
        )

    # Generate PyTeal and TEAL for the recurive Euclidean algorithm:
    euclid_app = blackbox_pyteal(euclid, Mode.Application)
    euclid_app_teal = compileTeal(euclid_app(), Mode.Application, version=6)

    # Execute on the input sequence to get a dry-run inspectors:
    algod = algod_with_assertion()
    inspectors = DryRunExecutor.dryrun_app_on_sequence(algod, euclid_app_teal, inputs)

    # Assert that each invarient holds on the sequences of inputs and dry-runs:
    for property, predicate in predicates.items():
        Invariant(predicate).validates(property, inputs, inspectors)


@pytest.mark.parametrize(
    "example",
    [blackbox_pyteal_example1, blackbox_pyteal_example2, blackbox_pyteal_example3],
)
def test_blackbox_pyteal_examples(example):
    example()


@pytest.mark.parametrize("snippet", [user_guide_snippet_dynamic_scratch_var])
def test_user_guide_snippets(snippet):
    assert_new_v_old(snippet, version=6)
