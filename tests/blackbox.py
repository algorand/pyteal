from typing import Callable, Generic, Sequence, TypeVar, cast
from dataclasses import dataclass

import algosdk.abi
from algosdk.v2client import algod

from graviton import blackbox
from graviton.blackbox import DryRunInspector, DryRunExecutor

from pyteal.ast.subroutine import OutputKwArgInfo

from pyteal import (
    abi,
    Arg,
    Btoi,
    Bytes,
    compileTeal,
    Expr,
    Int,
    Itob,
    Len,
    Log,
    Mode,
    Pop,
    ScratchVar,
    Seq,
    SubroutineFnWrapper,
    TealType,
    Txn,
)

from pyteal.ast.subroutine import ABIReturnSubroutine

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
    def __init__(
        self,
        subr: SubroutineFnWrapper | ABIReturnSubroutine,
        input_types: list[TealType | None],
    ):
        subr.subroutine._validate(input_types=input_types)
        self.subroutine: SubroutineFnWrapper | ABIReturnSubroutine = subr
        self.input_types: list[TealType | abi.TypeSpec | None] = self._fill(input_types)

    def __call__(self, *args: Expr | ScratchVar, **kwargs) -> Expr | abi.ReturnedValue:
        return self.subroutine(*args, **kwargs)

    def name(self) -> str:
        return self.subroutine.name()

    def _fill(
        self, input_types: list[TealType | None]
    ) -> list[TealType | abi.TypeSpec | None]:
        match self.subroutine:
            case SubroutineFnWrapper() | ABIReturnSubroutine():
                args = self.subroutine.subroutine.arguments()
                abis = self.subroutine.subroutine.abi_args
                return [(x if x else abis[args[i]]) for i, x in enumerate(input_types)]
            case _:
                raise AssertionError(
                    f"Cannot handle subroutine of type {type(self.subroutine)}"
                )


def Blackbox(input_types: list[TealType | None]):
    """
    Decorator for transforming @Subroutine and @ABIReturnSubroutine wrapped functions
    into PyTeal expressions that compile into executable Teal programs.

    input_types: list[TealType] (required)
        List shadowing the input arguments of the decorated subroutine. In particular:
            * the list needs to be the same length as the number of subroutine arguments
            * if the subroutine argument is an ABI type, the shadowing input_type must be None
                as it will be determined at compile time from the subroutine's annotation
            * if the subroutine argument is an Expr or a ScratchVar, the shadowing input_type
                must be a TealType of the same kind as expected in the argument

    Some _Correct_ Examples:

    @Blackbox(input_types=[TealType.bytes, TealType.uint64])
    @Subroutine(TealType.bytes)
    def string_mult(x, y):
        ...

    @Blackbox(input_types=[TealType.bytes, TealType.uint64])
    @Subroutine(TealType.bytes)
    def string_mult(x: Expr, y: Expr):
        ...

    @Blackbox(input_types=[TealType.bytes, TealType.uint64])
    @Subroutine(TealType.bytes)
    def string_mult(x: ScratchVar, y: Expr):
        ...


    @Blackbox(input_types=[None, None])
    @ABIReturnSubroutine
    def string_mult(x: abi.String, y: abi.Uint16):
        ...

    @Blackbox(input_types=[None, TealType.uint64])
    @ABIReturnSubroutine
    def string_mult(x: abi.String, y):
        ...

    @Blackbox([None])
    @Subroutine(TealType.uint64)
    def cubed(n: abi.Uint64):
        ...

    """

    def decorator_blackbox(func: SubroutineFnWrapper | ABIReturnSubroutine):
        return BlackboxWrapper(func, input_types)

    return decorator_blackbox


# ---- API ---- #


Output = TypeVar("Output")
Lazy = Callable[[], Output]


@dataclass(frozen=True)
class _MatchMode(Generic[Output]):
    app_case: Lazy
    signature_case: Lazy

    def __call__(self, mode: Mode, *args, **kwargs) -> Output:
        match mode:
            case Mode.Application:
                return self.app_case()
            case Mode.Signature:
                return self.signature_case()
            case _:
                raise Exception(f"Unknown mode {mode} of type {type(mode)}")


def mode_to_execution_mode(mode: Mode) -> blackbox.ExecutionMode:
    return _MatchMode(
        app_case=lambda: blackbox.ExecutionMode.Application,
        signature_case=lambda: blackbox.ExecutionMode.Signature,
    )(mode)


class PyTealDryRunExecutor:
    def __init__(self, subr: BlackboxWrapper, mode: Mode):
        """
        Args:
            subr: a Subroutine or ABIReturnSubroutine which has been decorated with @Blackbox.
                Note: the `input_types` parameters should be supplied to the @Blackbox() decorator
                    cf. the Blackbox class for futher details about acceptable `input_types`

            mode: type of program to produce: logic sig (Mode.Signature) or app (Mode.Application)
        """
        input_types = subr.input_types
        assert (
            input_types is not None
        ), "please provide input_types in your @Subroutine or @ABIReturnSubroutine annotation (this is crucial for generating proper end-to-end testable PyTeal)"

        self.subr, self.mode, self.input_types = subr, mode, input_types
        match subr.subroutine:
            case SubroutineFnWrapper():
                approval = self._handle_SubroutineFnWrapper()
            case ABIReturnSubroutine():
                approval = self._handle_ABIReturnSubroutine()
            case _:
                raise AssertionError(
                    f"Cannot produce Blackbox pyteal for provided subroutine of type {type(subr.subroutine)}"
                )

        self._pyteal_lambda: Callable[..., Expr] = approval

    def is_abi(self) -> bool:
        return isinstance(self.subr.subroutine, ABIReturnSubroutine)

    def abi_argument_types(self) -> None | list[algosdk.abi.ABIType]:
        if not (self.input_types or self.is_abi()):
            return None

        def handle_arg(arg):
            if isinstance(arg, abi.TypeSpec):
                return abi.algosdk_from_type_spec(arg)
            return None

        return [handle_arg(arg) for arg in self.input_types]

    def abi_return_type(self) -> None | algosdk.abi.ABIType:
        if not self.is_abi():
            return None

        out_info = getattr(self.subr.subroutine, "output_kwarg_info")
        if not out_info:
            return None

        return abi.algosdk_from_type_spec(cast(OutputKwArgInfo, out_info).abi_type)

    def program(self) -> Expr:
        """Get ready-to-compile PyTeal program from Subroutines and ABIReturnSubroutines

        Returns:
            a PyTeal expression representing a ready-to-run TEAL program

        Generated TEAL code depends on the self.subr's type, the mode, the input types, and output type
        * logic sigs:
            * input received via `arg i`
            * args are converted (cf. "input conversion" below) and passed to the subroutine
            * subroutine output is not logged (log is not available)
            * in the case of ABIReturnSubroutine: the output is encoded on to the stack an then popped off
            * subroutine output is converted (cf "output conversion" below)
        * apps:
            * input received via `txna ApplicationArgs i`
            * args are converted (cf. "input conversion" below) and passed to the subroutine
            * the output is logged in the following ways:
                * Subroutine: logged after possible conversion (cf. "logging conversion")
                * ABIReturnSubroutine: the encoded output is concatenated to the return method selector and then logged
            * subroutine output is converted (cf "output conversion" below) (Subroutine case only)
        * input conversion:
            * Empty input array:
                do not read any args and call subroutine immediately
            * Expr arg of TealType.bytes and TealType.anytype:
                read arg and pass to subroutine as is
            * Expr arg of TealType.uint64:
                convert arg to int using Btoi() when received
            * pass-by-ref ScratchVar arguments:
                in addition to the above -
                    o store the arg (or converted arg) in a ScratchVar
                    o invoke the subroutine using this ScratchVar instead of the arg (or converted arg)
            * ABI arguments:
                in addition to the above -
                    o store the decoded arg into the ScratchVar of an ABI Type instance
                    o invoke the subroutine using this ABI Type instead of the arg
        * output conversion:
            * Subroutine case:
                * TealType.uint64:
                    provide subroutine's result to the top of the stack when exiting program
                * TealType.bytes:
                    convert subroutine's result to the top of the stack to its length and then exit
                * TealType.none or TealType.anytype:
                    push Int(1337) to the stack as it is either impossible (TealType.none),
                    or unknown at compile time (TealType.anytype) to convert to an Int
            * ABIReturnSubroutine case:
                * when present, the output is encoded as TealType.bytes which can be decoded by the receiver using
                appropriate ABI-libraries
        * logging conversion:
            * Subroutine case:
                * TealType.uint64:
                    convert subroutine's output using Itob() and log the result
                * TealType.bytes:
                    log the subroutine's result
                * TealType.none or TealType.anytype:
                    log Itob(Int(1337)) as it is either impossible (TealType.none),
                    or unknown at compile time (TealType.anytype) how to convert to Bytes
            * ABIReturnSubroutine case:
                * when present, the output is encoded as TealType.bytes and concatenated to the rewturn
                method selector. This can be decoded by the receiver using appropriate ABI-libraries

        For illustrative examples of how to use this method please refer to the integration test file `graviton_test.py` and especially:

        * `blackbox_pyteal_example1()`: Using blackbox_pyteal() for a simple test of both an app and logic sig
        * `blackbox_pyteal_example2()`: Using blackbox_pyteal() to make 400 assertions and generate a CSV report with 400 dryrun rows
        * `blackbox_pyteal_example3()`: declarative Test Driven Development approach through Invariant's
        * `blackbox_pyteal_example4()`: Using PyTealDryRunExecutor to debug an ABIReturnSubroutine with an app, logic sig and csv reports
        """

        return self._pyteal_lambda()

    def _arg_prep_n_call(self, i, p):
        subdef = self.subr.subroutine.subroutine
        arg_names = subdef.arguments()
        name = arg_names[i]
        arg_expr = Txn.application_args[i] if self.mode == Mode.Application else Arg(i)
        if p == TealType.uint64:
            arg_expr = Btoi(arg_expr)

        if name in subdef.by_ref_args:
            arg_var = ScratchVar(p)
            prep = arg_var.store(arg_expr)
        elif name in subdef.abi_args:
            arg_var = p.new_instance()
            prep = arg_var.decode(arg_expr)
        else:
            arg_var = arg_expr
            prep = None
        return prep, arg_var

    def _prepare_n_calls(self):
        preps_n_calls = [
            *(self._arg_prep_n_call(i, p) for i, p in enumerate(self.input_types))
        ]
        preps, calls = zip(*preps_n_calls) if preps_n_calls else ([], [])
        preps = [p for p in preps if p]
        return preps, calls

    def _handle_SubroutineFnWrapper(self):
        subdef = self.subr.subroutine.subroutine

        def subr_caller():
            preps, calls = self._prepare_n_calls()
            invocation = self.subr(*calls)
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

        if self.mode == Mode.Signature:

            def approval():
                return make_return(subr_caller())

        else:

            def approval():
                if subdef.return_type == TealType.none:
                    result = ScratchVar(TealType.uint64)
                    part1 = [subr_caller(), result.store(Int(1337))]
                else:
                    result = ScratchVar(subdef.return_type)
                    part1 = [result.store(subr_caller())]

                part2 = [make_log(result.load()), make_return(result.load())]
                return Seq(*(part1 + part2))

        return approval

    def _handle_ABIReturnSubroutine(self):
        output = None
        if self.subr.subroutine.output_kwarg_info:
            output = self.subr.subroutine.output_kwarg_info.abi_type.new_instance()

        def approval():
            preps, calls = self._prepare_n_calls()

            # when @ABIReturnSubroutine is void:
            #   invocation is an Expr of TealType.none
            # otherwise:
            #   it is a ComputedValue
            invocation = self.subr(*calls)
            if output:
                invocation = output.set(invocation)
                if self.mode == Mode.Signature:
                    results = [invocation, Pop(output.encode()), Int(1)]
                else:
                    results = [invocation, abi.MethodReturn(output), Int(1)]
            else:
                results = [invocation, Int(1)]

            return Seq(*(preps + results))

        return approval

    def compile(self, version: int, assemble_constants: bool = False) -> str:
        return _MatchMode(
            app_case=lambda: compileTeal(
                self.program(),
                self.mode,
                version=version,
                assembleConstants=assemble_constants,
            ),
            signature_case=lambda: compileTeal(
                self.program(),
                self.mode,
                version=version,
                assembleConstants=assemble_constants,
            ),
        )(self.mode)

    def dryrun_on_sequence(
        self,
        inputs: list[Sequence[str | int]],
        compiler_version=6,
    ) -> list[DryRunInspector]:
        return _MatchMode(
            app_case=lambda: DryRunExecutor.dryrun_app_on_sequence(
                algod_with_assertion(),
                self.compile(compiler_version),
                inputs,
                self.abi_argument_types(),
                self.abi_return_type(),
            ),
            signature_case=lambda: DryRunExecutor.dryrun_logicsig_on_sequence(
                algod_with_assertion(),
                self.compile(compiler_version),
                inputs,
                self.abi_argument_types(),
                self.abi_return_type(),
            ),
        )(self.mode)

    def dryrun(
        self,
        args: Sequence[bytes | str | int],
        compiler_version=6,
    ) -> DryRunInspector:
        return _MatchMode(
            app_case=lambda: DryRunExecutor.dryrun_app(
                algod_with_assertion(),
                self.compile(compiler_version),
                args,
                self.abi_argument_types(),
                self.abi_return_type(),
            ),
            signature_case=lambda: DryRunExecutor.dryrun_logicsig(
                algod_with_assertion(),
                self.compile(compiler_version),
                args,
                self.abi_argument_types(),
                self.abi_return_type(),
            ),
        )(self.mode)
