from typing import Callable, Dict, List, Union

from algosdk import kmd
from algosdk.v2client import algod, indexer

import algosdk.testing.teal_blackbox as blackbox

from pyteal import *

## Clients


def _algod_client(
    algod_address="http://localhost:4001", algod_token="a" * 64
) -> algod.AlgodClient:
    """Instantiate and return Algod client object."""
    return algod.AlgodClient(algod_token, algod_address)


def _kmd_client(
    kmd_address="http://localhost:4002", kmd_token="a" * 64
) -> kmd.KMDClient:
    """Instantiate and return a KMD client object."""
    return kmd.KMDClient(kmd_token, kmd_address)


def _indexer_client(
    indexer_address="http://localhost:8980", indexer_token="a" * 64
) -> indexer.IndexerClient:
    """Instantiate and return Indexer client object."""
    return indexer.IndexerClient(indexer_token, indexer_address)


def algod_with_assertion():
    algod = _algod_client()
    assert algod.status(), "alod.status() did not produce any results"
    return algod


def mode_to_execution_mode(mode: Mode) -> blackbox.ExecutionMode:
    if mode == Mode.Application:
        return blackbox.ExecutionMode.Application
    if mode == Mode.Signature:
        return blackbox.ExecutionMode.Signature

    raise Exception(f"Unknown mode {mode} of type {type(mode)}")


def e2e_pyteal(subr: SubroutineFnWrapper, mode: Mode) -> Callable[..., Expr]:
    """Functor producing ready-to-compile PyTeal programs from annotated subroutines

    Args:
        subr: annotated subroutine to wrap inside program.
            Note: the `input_types` parameters should be supplied to @Subroutine() annotation
        mode: type of program to produce: logic sig (Mode.Signature) or app (Mode.Application)

    Returns:
        a function that called with no parameters -e.g. result()-
        returns a PyTeal expression compiling to a ready-to-test E2E TEAL program.

    The return type is callable in order to adhere to the API of end-to-end unit tests.

    Generated TEAL code depends on the mode, subroutine input types, and subroutine output types.
    * logic sigs:
        * input received via `arg i`
        * args are converted (cf. "input conversion" below) and passed to the subroutine
        * subroutine output is not logged (log is not available)
        * subroutine output is converted (cf "output conversion" below)
    * apps:
        * input received via `txna ApplicationArgs i`
        * args are converted (cf. "input conversion" below) and passed to the subroutine
        * subroutine output is logged after possible conversion (cf. "logging coversion")
        * subroutine output is converted (cf "output conversion" below)
    * input conversion:
        * Empty input array:
            do not read any args and call subroutine immediately
        * arg of TealType.bytes and TealType.any:
            read arg and pass to subroutine as is
        * arg of TealType.uint64:
            convert arg to int using Btoi() when received
    * output conversion:
        * TealType.uint64:
            provide subroutine's result to the top of the stack when exiting program
        * TealType.bytes:
            convert subroutine's result to the top of the stack to its length and then exit
        * TealType.none or TealType.anytype:
            push Int(1337) to the stack as it is either impossible (TealType.none),
            or unknown at compile time (TealType.any) to convert to an Int
    * logging conversion:
        * TealType.uint64:
            convert subroutine's output using Itob() and log the result
        * TealType.bytes:
            log the subroutine's result
        * TealType.none or TealType.anytype:
            log Itob(Int(1337)) as it is either impossible (TealType.none),
            or unknown at compile time (TealType.any) how to convert to Bytes


    Example 1: Using e2e_pyteal for a simple test of both an app and logic sig:
        .. code-block:: python
            from algosdk.testing.teal_blackbox import (
                DryRunEncoder,
                DryRunExecutor as Executor,
            )

            @Subroutine(TealType.uint64, input_types=[TealType.uint64])
            def square(x):
                return x ** Int(2)

            # use this function to create pyteal app and signature expression approval functions:
            approval_app = e2e_pyteal(square, Mode.Application)
            approval_lsig = e2e_pyteal(square, Mode.Signature)

            # compile the evaluated approvals to generate TEAL code
            app_teal = compileTeal(approval_app(), Mode.Application, version=6)
            lsig_teal = compileTeal(approval_lsig(), Mode.Signature, version=6)

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

    Example 2: Using e2e_pyteal to make 400 assertions and generate a CSV report with 400 dryrun rows
        .. code-block:: python
            from itertools import product
            import math
            from pathlib import Path
            import random

            from algosdk.testing.teal_blackbox import (
                DryRunExecutor as Executor,
            )

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
                return Seq(For(start, cond, step).Do(Pop(Int(1))), a.load())

            euclid_app = e2e_pyteal(euclid, Mode.Application)
            euclid_app_teal = compileTeal(euclid_app(), Mode.Application, version=6)

            # generate a report with 400 = 20*20 dry run rows:
            N = 20
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

    Example 3: Declarative Sequence Assertions with e2e_pyteal
        .. code-block:: python
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
                    DRProp.noError: True,
                },
            }

            exec_mode = mode_to_execution_mode(Mode.Application)
            inputs, assertions = SequenceAssertion.inputs_and_assertions(scenario, exec_mode)
            euclid_results = Executor.dryrun_app_on_sequence(algod, euclid_app_teal, inputs)
            for assert_type, predicate in assertions.items():
                assertion = SequenceAssertion(predicate, name=str(assert_type))
                assertion.dryrun_assert(inputs, euclid_results, assert_type)
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
        # TealType.anytype:
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
