from typing import Callable

from algosdk.v2client import algod

from graviton import blackbox

from pyteal import (
    Arg,
    Btoi,
    Bytes,
    Expr,
    Int,
    Itob,
    Len,
    Log,
    Mode,
    ScratchVar,
    Seq,
    SubroutineFnWrapper,
    TealType,
    Txn,
)

# ---- Clients ---- #


def algod_client(
    algod_address="http://localhost:4001", algod_token="a" * 64
) -> algod.AlgodClient:
    """Instantiate and return Algod client object."""
    return algod.AlgodClient(algod_token, algod_address)


def algod_with_assertion():
    algod = algod_client()
    assert algod.status(), "algod.status() did not produce any results"
    return algod


# ---- API ---- #


def mode_to_execution_mode(mode: Mode) -> blackbox.ExecutionMode:
    if mode == Mode.Application:
        return blackbox.ExecutionMode.Application
    if mode == Mode.Signature:
        return blackbox.ExecutionMode.Signature

    raise Exception(f"Unknown mode {mode} of type {type(mode)}")


def blackbox_pyteal(subr: SubroutineFnWrapper, mode: Mode) -> Callable[..., Expr]:
    """Functor producing ready-to-compile PyTeal programs from annotated subroutines

    Args:
        subr: annotated subroutine to wrap inside program.
            Note: the `input_types` parameters should be supplied to @Subroutine() annotation
        mode: type of program to produce: logic sig (Mode.Signature) or app (Mode.Application)

    Returns:
        a function that called with no parameters -e.g. result()-
        returns a PyTeal expression compiling to a ready-to-test TEAL program.

    The return type is callable in order to adhere to the API of blackbox tests.

    Generated TEAL code depends on the mode, subroutine input types, and subroutine output types.
    * logic sigs:
        * input received via `arg i`
        * args are converted (cf. "input conversion" below) and passed to the subroutine
        * subroutine output is not logged (log is not available)
        * subroutine output is converted (cf "output conversion" below)
    * apps:
        * input received via `txna ApplicationArgs i`
        * args are converted (cf. "input conversion" below) and passed to the subroutine
        * subroutine output is logged after possible conversion (cf. "logging conversion")
        * subroutine output is converted (cf "output conversion" below)
    * input conversion:
        * Empty input array:
            do not read any args and call subroutine immediately
        * arg of TealType.bytes and TealType.anytype:
            read arg and pass to subroutine as is
        * arg of TealType.uint64:
            convert arg to int using Btoi() when received
        * pass-by-ref ScratchVar arguments:
            in addition to the above -
                o store the arg (or converted arg) in a ScratchVar
                o invoke the subroutine using this ScratchVar instead of the arg (or converted arg)
    * output conversion:
        * TealType.uint64:
            provide subroutine's result to the top of the stack when exiting program
        * TealType.bytes:
            convert subroutine's result to the top of the stack to its length and then exit
        * TealType.none or TealType.anytype:
            push Int(1337) to the stack as it is either impossible (TealType.none),
            or unknown at compile time (TealType.anytype) to convert to an Int
    * logging conversion:
        * TealType.uint64:
            convert subroutine's output using Itob() and log the result
        * TealType.bytes:
            log the subroutine's result
        * TealType.none or TealType.anytype:
            log Itob(Int(1337)) as it is either impossible (TealType.none),
            or unknown at compile time (TealType.anytype) how to convert to Bytes


    Example 1: Using blackbox_pyteal for a simple test of both an app and logic sig:
        .. code-block:: python
            from graviton.blackbox import DryRunEncoder, DryRunExecutor

            from pyteal import compileTeal, Int, Mode, Subroutine, TealType
            from utils.blackbox import algod_with_assertion, blackbox_pyteal

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


    Example 2: Using blackbox_pyteal to make 400 assertions and generate a CSV report with 400 dryrun rows
        .. code-block:: python
            from itertools import product
            import math
            from pathlib import Path
            import random

            from graviton.blackbox import DryRunExecutor, DryRunInspector

            from pyteal import (
                compileTeal,
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

            from utils.blackbox import algod_with_assertion, blackbox_pyteal

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


    Example 3: Declarative Sequence Assertions with blackbox_pyteal
        .. code-block:: python
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

            from pyteal import compileTeal, If, Int, Mod, Mode, Subroutine, TealType

            from utils.blackbox import (
                algod_with_assertion,
                blackbox_pyteal,
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

            # Generate PyTeal and TEAL for the recursive Euclidean algorithm:
            euclid_app = blackbox_pyteal(euclid, Mode.Application)
            euclid_app_teal = compileTeal(euclid_app(), Mode.Application, version=6)

            # Execute on the input sequence to get a dry-run inspectors:
            algod = algod_with_assertion()
            inspectors = DryRunExecutor.dryrun_app_on_sequence(algod, euclid_app_teal, inputs)

            # Assert that each invarient holds on the sequences of inputs and dry-runs:
            for property, predicate in predicates.items():
                Invariant(predicate).validates(property, inputs, inspectors)
    """
    input_types = subr.subroutine.input_types
    assert (
        input_types is not None
    ), "please provide input_types in your @Subroutine annotation (crucial for generating proper end-to-end testable PyTeal)"

    arg_names = subr.subroutine.arguments()

    def arg_prep_n_call(i, p):
        name = arg_names[i]
        by_ref = name in subr.subroutine.by_ref_args
        arg_expr = Txn.application_args[i] if mode == Mode.Application else Arg(i)
        if p == TealType.uint64:
            arg_expr = Btoi(arg_expr)
        prep = None
        arg_var = arg_expr
        if by_ref:
            arg_var = ScratchVar(p)
            prep = arg_var.store(arg_expr)
        return prep, arg_var

    def subr_caller():
        preps_n_calls = [*(arg_prep_n_call(i, p) for i, p in enumerate(input_types))]
        preps, calls = zip(*preps_n_calls) if preps_n_calls else ([], [])
        preps = [p for p in preps if p]
        invocation = subr(*calls)
        if preps:
            return Seq(*(preps + [invocation]))
        return invocation

    def make_return(e):
        if e.type_of() == TealType.uint64:
            return e
        if e.type_of() == TealType.bytes:
            return Len(e)
        if e.type_of() == TealType.anytype:
            x = ScratchVar(TealType.anytype)
            return Seq(x.store(e), Int(1337))
        # TealType.none:
        return Seq(e, Int(1337))

    def make_log(e):
        if e.type_of() == TealType.uint64:
            return Log(Itob(e))
        if e.type_of() == TealType.bytes:
            return Log(e)
        return Log(Bytes("nada"))

    if mode == Mode.Signature:

        def approval():
            return make_return(subr_caller())

    else:

        def approval():
            if subr.subroutine.returnType == TealType.none:
                result = ScratchVar(TealType.uint64)
                part1 = [subr_caller(), result.store(Int(1337))]
            else:
                result = ScratchVar(subr.subroutine.returnType)
                part1 = [result.store(subr_caller())]

            part2 = [make_log(result.load()), make_return(result.load())]
            return Seq(*(part1 + part2))

    setattr(approval, "__name__", f"sem_{mode}_{subr.name()}")
    return approval
