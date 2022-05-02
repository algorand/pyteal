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


def algod_with_assertion():
    algod = _algod_client()
    assert algod.status(), "algod.status() did not produce any results"
    return algod


def _algod_client(
    algod_address="http://localhost:4001", algod_token="a" * 64
) -> algod.AlgodClient:
    """Instantiate and return Algod client object."""
    return algod.AlgodClient(algod_token, algod_address)


# ---- Decorator ---- #


class BlackboxWrapper:
    def __init__(self, subr: SubroutineFnWrapper, input_types: list[TealType]):
        subr.subroutine._validate(input_types=input_types)
        self.subroutine = subr
        self.input_types = input_types

    def __call__(self, *args: Expr | ScratchVar, **kwargs) -> Expr:
        return self.subroutine(*args, **kwargs)

    def name(self) -> str:
        return self.subroutine.name()


def Blackbox(input_types: list[TealType]):
    def decorator_blackbox(func: SubroutineFnWrapper):
        return BlackboxWrapper(func, input_types)

    return decorator_blackbox


# ---- API ---- #


def mode_to_execution_mode(mode: Mode) -> blackbox.ExecutionMode:
    if mode == Mode.Application:
        return blackbox.ExecutionMode.Application
    if mode == Mode.Signature:
        return blackbox.ExecutionMode.Signature

    raise Exception(f"Unknown mode {mode} of type {type(mode)}")


def blackbox_pyteal(subr: BlackboxWrapper, mode: Mode) -> Callable[..., Expr]:
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

    For illustrative examples of how to use this function please refer to the integration test file `graviton_test.py` and especially:

    * `blackbox_pyteal_example1()`: Using blackbox_pyteal() for a simple test of both an app and logic sig
    * `blackbox_pyteal_example2()`: Using blackbox_pyteal() to make 400 assertions and generate a CSV report with 400 dryrun rows
    * `blackbox_pyteal_example3()`: declarative Test Driven Development approach through Invariant's
    """
    input_types = subr.input_types
    assert (
        input_types is not None
    ), "please provide input_types in your @Subroutine annotation (crucial for generating proper end-to-end testable PyTeal)"

    subdef = subr.subroutine.subroutine
    arg_names = subdef.arguments()

    def arg_prep_n_call(i, p):
        name = arg_names[i]
        by_ref = name in subdef.by_ref_args
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
            if subdef.returnType == TealType.none:
                result = ScratchVar(TealType.uint64)
                part1 = [subr_caller(), result.store(Int(1337))]
            else:
                result = ScratchVar(subdef.returnType)
                part1 = [result.store(subr_caller())]

            part2 = [make_log(result.load()), make_return(result.load())]
            return Seq(*(part1 + part2))

    setattr(approval, "__name__", f"sem_{mode}_{subr.name()}")
    return approval
