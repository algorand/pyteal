from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, asdict
import json
from typing import Any, Callable, Final, Literal, Sequence, Type, cast

import algosdk.abi as sdk_abi
from algosdk.transaction import OnComplete
from algosdk import v2client

from graviton import blackbox
from graviton.abi_strategy import (
    ABIArgsMod,
    ABICallStrategy,
    ABIStrategy,
    RandomArgLengthCallStrategy,
)
from graviton.blackbox import (
    DryRunInspector,
    DryRunExecutor,
    DryRunTransactionParams as TxParams,
)
from graviton.inspector import DryRunProperty as DRProp
from graviton.models import ExecutionMode, PyTypes
from graviton.sim import InputStrategy, Simulation, SimulationResults

from pyteal.compiler.compiler import OptimizeOptions
from pyteal.ast.subroutine import OutputKwArgInfo

from pyteal import (
    abi,
    Arg,
    Btoi,
    Bytes,
    CallConfig,
    compileTeal,
    Expr,
    Int,
    Itob,
    Len,
    Log,
    MethodConfig,
    Mode,
    Pop,
    Router,
    ScratchVar,
    Seq,
    SubroutineFnWrapper,
    TealType,
    Txn,
)

from pyteal.ast.subroutine import ABIReturnSubroutine

# ---- Types ---- #

Predicates = dict[DRProp, Any]  # same as in graviton


CLEAR_STATE_CALL: Final[str] = "ClearStateCall"
ClearStateCallType = Literal["ClearStateCall"]

# str for methods, None for bare app calls:
CallType = str | None

# CallType for app calls, CLEAR_STATE_CALL for clear state calls:
RouterCallType = CallType | ClearStateCallType  # type: ignore

ABICallConfigs = dict[CallType, MethodConfig]

# key `method_config == None` indicates that the MethodConfig's
# should be picked up from the router
CallPredicates = dict[RouterCallType, Predicates]

# ---- Clients ---- #


def algod_with_assertion():
    algod = _algod_client()
    assert algod.status(), "algod.status() did not produce any results"
    return algod


def _algod_client(
    algod_address="http://localhost:4001", algod_token="a" * 64
) -> v2client.algod.AlgodClient:
    """Instantiate and return Algod client object."""
    return v2client.algod.AlgodClient(algod_token, algod_address)


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


def mode_to_execution_mode(mode: Mode) -> blackbox.ExecutionMode:
    if mode == Mode.Application:
        return blackbox.ExecutionMode.Application
    if mode == Mode.Signature:
        return blackbox.ExecutionMode.Signature

    raise ValueError(f"Can't handle {mode=}")


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
        assert input_types is not None, (
            "please provide input_types in your @Subroutine or @ABIReturnSubroutine "
            "annotation. "
            "(this is crucial for generating proper end-to-end testable PyTeal)"
        )

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

        self.traces: list = []

    def add_trace(self, trace: Any) -> None:
        self.traces.append(trace)

    def is_abi(self) -> bool:
        return isinstance(self.subr.subroutine, ABIReturnSubroutine)

    def abi_method_signature(self) -> None | str:
        if self.is_abi():
            abi_subr = cast(ABIReturnSubroutine, self.subr.subroutine)
            return abi_subr.method_signature()

        # create an artificial method signature
        # based on the `abi_argument_types()` and `abi_return_type()`
        if arg_types := self.abi_argument_types():
            if all(t is None for t in arg_types):
                return None

            ret_type = self.abi_return_type()
            ret = str(ret_type) if ret_type else "void"
            return f"ptdre_foo({','.join(map(str, arg_types))}){ret}"

        return None

    def abi_argument_types(self) -> None | list[sdk_abi.ABIType]:
        if not (self.input_types or self.is_abi()):
            return None

        def handle_arg(arg):
            if isinstance(arg, abi.TypeSpec):
                return abi.algosdk_from_type_spec(arg)
            return None

        return [handle_arg(arg) for arg in self.input_types]

    def abi_return_type(self) -> None | sdk_abi.ABIType:
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
        return compileTeal(
            self.program(),
            self.mode,
            version=version,
            assembleConstants=assemble_constants,
        )

    def executor(self, compiler_version: int = 6) -> DryRunExecutor:
        return DryRunExecutor(
            algod=algod_with_assertion(),
            mode=mode_to_execution_mode(self.mode),
            teal=self.compile(compiler_version),
            abi_method_signature=self.abi_method_signature(),
            omit_method_selector=True,
        )

    def dryrun_sequence(
        self,
        inputs: list[Sequence[PyTypes]],
        *,
        compiler_version=6,
        txn_params: TxParams | None = None,
        verbose: bool = False,
    ) -> list[DryRunInspector]:
        return cast(
            list,
            self.executor(compiler_version).run_sequence(
                inputs, txn_params=txn_params, verbose=verbose
            ),
        )

    def dryrun_one(
        self,
        args: Sequence[bytes | str | int],
        *,
        compiler_version=6,
        txn_params: TxParams | None = None,
        verbose: bool = False,
    ) -> DryRunInspector:
        return self.executor(compiler_version).run_one(
            args, txn_params=txn_params, verbose=verbose
        )


def as_on_complete(oc_str: str) -> OnComplete:
    match oc_str:
        case "no_op":
            return OnComplete.NoOpOC
        case "opt_in":
            return OnComplete.OptInOC
        case "close_out":
            return OnComplete.CloseOutOC
        case "clear_state":
            return OnComplete.ClearStateOC
        case "update_application":
            return OnComplete.UpdateApplicationOC
        case "delete_application":
            return OnComplete.DeleteApplicationOC

    raise ValueError(f"unrecognized {oc_str=}")


def negate_cc(cc: CallConfig) -> CallConfig:
    return CallConfig(3 - cc)


@dataclass(frozen=True)
class RouterSimulationResults:
    stats: dict[str, Any]
    results: dict
    approval_simulator: Simulation | None
    clear_simulator: Simulation | None


class RouterSimulation:
    """
    Lifecycle of a RouterSimulation

    1. Creation (__init__ method):
        * router: Router (no version or other options specified)
        * predicates: CallPredicates - the Router ought satisfy. Type has shape:
            * method --> <property -> predicate ...> ...
        * model_router: Router (optional) - in the case when the predicates provided
            are of type PredicateKind.IdenticalPair, this parameter needs to be
            provided for comparison.
            NOTE: model_router may in fact be the same as router, and in this case
            it is expected that something else such as version or optimization option
            would differ between model_router and router during the simulation
        * algod (optional) - if missing, just get one

    Artifacts from Step 1 are stored in self.results: _SimConfig

    2. Simulation (simulate_and_assert method): - using self.results artifacts Step 1, also takes params:
        * approval_arg_strat_type: Type[ABICallStrategy]
            - strategy type to use for approval program's arg generation
        * clear_arg_strat_type_or_inputs: Type[ABICallStrategy] | Iterable[Sequence[PyTypes]] | None
            - strategy type to use for clear program's arg generation
        * approval_abi_args_mod: ABIArgsMod (default None)
            - used to specify any arg mutation
        # TODO: currently there aren't any clear_abi_args_mod, but we might need these for testing non-trivial clear programs
        * version: int - for compiling self.router
        * method_configs: ABICallConfigs - these drive all the test cases
        * assemble_constants: bool (optional) - for compiling self.router
        * optimize: OptimizeOptions (optional) - for compiling self.router
        * num_dryruns: int (default 1)
            - the number of input runs to generate per method X config combination
        * txn_params: TxParams (optional)
            - other TxParams to append in addition to the (is_app_create, OnComplete) information
        * model_version: int - for compiling self.model_router
        * model_assemble_constants: bool (optional) - for compiling self.model_router
        * model_optimize: OptimizeOptions (optional) - for compiling self.model_router
        * msg: string (optional) - message to report when an assertion is violated
        * omit_approval_call: bool (default False) - allow purely testing the clear program
        * omit_clear_call: bool (default False) - allow purely testing the approval program
        NOTE: one of omit_approval_call or omit_clear_call must remain False
        * executor_validation (default True) - when False, skip the DryRunExecutor's validation
        * skip_validation (default False) - when False, skip the Router's validation
    """

    def __init__(
        self,
        router: Router,
        predicates: CallPredicates,
        *,
        model_router: Router | None = None,
        algod: v2client.algod.AlgodClient | None = None,
    ):
        self.router: Router = self._validate_router(router)

        self.predicates: CallPredicates = self._validate_predicates(predicates)

        self.model_router: Router | None = None
        if model_router:
            self.model_router = self._validate_router(model_router, kind="Model")

        self.algod: v2client.algod.AlgodClient = algod or algod_with_assertion()

        self.results: dict[
            str | None, dict[tuple[bool, OnComplete], SimulationResults]
        ] = {}

    # ---- Validation ---- #

    @classmethod
    def _validate_router(cls, router: Router, kind: str = "Base") -> Router:
        assert isinstance(
            router, Router
        ), f"Wrong type for {kind} Router: {type(router)}"
        cls._validate_method_configs(router.method_configs)

        return router

    @classmethod
    def _validate_method_configs(cls, method_configs):
        assert isinstance(
            method_configs, dict
        ), f"method_configs '{method_configs}' has type {type(method_configs)} but only 'dict' and 'NoneType' are allowed."

        assert (
            method_configs
        ), "make sure to give at least one key/value pair in method_configs"

        for call, meth_config in method_configs.items():
            assert isinstance(  # type: ignore
                call, CallType
            ), f"method_configs dict key '{call}' has type {type(call)} but only str and NoneType are allowed."
            cls._validate_single_method_config(call, meth_config)

    @classmethod
    def _validate_single_method_config(cls, call, meth_config):
        assert isinstance(
            meth_config, MethodConfig
        ), f"method_configs['{call}'] = has type {type(meth_config)} but only MethodConfig is allowed."
        assert (
            not meth_config.is_never()
        ), f"method_configs['{call}'] specifies NEVER to be called; for driving the test, each configured method should ACTUALLY be tested."
        assert (
            meth_config.clear_state is CallConfig.NEVER
        ), "unexpected value for method_config's clear_state"

    @classmethod
    def _validate_predicates(cls, predicates):
        assert isinstance(predicates, dict), (
            f"Wrong type for predicates: {type(predicates)}. Please provide: "
            f"dict[str | None, dict[graviton.DryRunProporty, Any]."
        )

        assert (
            len(predicates) > 0
        ), "Please provide at least one method to call and assert against."

        for method, preds in predicates.items():
            assert isinstance(method, (str, type(None), type(ClearStateCallType))), (
                f"Predicates method '{method}' has type {type(method)} but only "
                "'str' and 'NoneType' and Literal['ClearStateCall'] (== ClearStateCall)"
                " are allowed."
            )
            if isinstance(method, type(ClearStateCallType)):
                assert method == ClearStateCallType, (
                    f"Predicates method '{method}' is not allowed. "
                    "Only Literal['ClearStateCall'] (== ClearStateCall) "
                    "is allowed for a Literal."
                )
            assert (
                preds
            ), f"Every method must provide at least one predicate for assertion but method '{method}' is missing predicates."
            assert isinstance(
                preds, dict
            ), f"Method '{method}' is expected to have dict[graviton.DryRunProperty, Any] for its predicates value but the type is {type(preds)}."
            for prop in preds:
                assert isinstance(
                    prop, DRProp
                ), f"Method '{method}' is expected to have dict[graviton.DryRunProperty, Any] for its predicates value but predicates['{method}'] has key '{prop}' of {type(prop)}."

        return predicates

    def _validate_simulation(
        self,
        approval_args_strat_type,
        clear_args_strat_type,
        approval_abi_args_mod,
        num_dryruns,
        txn_params,
        model_version,
        method_configs,
        contract,
        model_contract,
        omit_clear_call,
    ):
        assert isinstance(approval_args_strat_type, type) and issubclass(
            approval_args_strat_type, ABIStrategy
        ), f"approval_args_strat_type should _BE_ a subtype of ABIStrategy but we have {approval_args_strat_type} (its type is {type(approval_args_strat_type)})."
        if not omit_clear_call:
            assert isinstance(clear_args_strat_type, type) and issubclass(
                clear_args_strat_type, ABIStrategy
            ), f"clear_args_strat_type should _BE_ a subtype of ABIStrategy but we have {clear_args_strat_type} (its type is {type(clear_args_strat_type)})."

        assert isinstance(
            approval_abi_args_mod, (ABIArgsMod, type(None))
        ), f"approval_abi_args_mod '{approval_abi_args_mod}' has type {type(approval_abi_args_mod)} but only 'ABIArgsMod' and 'NoneType' are allowed."

        self._validate_method_configs(method_configs)

        self._validate_meths_in_contract(method_configs, contract)

        if model_contract:
            self._validate_meths_in_contract(
                method_configs, model_contract, router_prefix="model"
            )

        assert (
            isinstance(num_dryruns, int) and num_dryruns >= 1
        ), f"num_dryruns must be a positive int but is {num_dryruns}."

        assert isinstance(
            txn_params, (TxParams, type(None))
        ), f"txn_params must have type DryRunTransactionParams or NoneType but has type {type(txn_params)}."

        if not self.model_router:
            assert (
                model_version is None
            ), f"model_version '{model_version}' was provided which is nonsensical because model_router was never provided for."

    def _validate_meths_in_contract(
        self, method_configs, contract, router_prefix="base"
    ):
        for meth in method_configs:
            if meth is None:
                continue
            try:
                contract.get_method_by_name(meth)
            except KeyError:
                raise ValueError(
                    f"method_configs has a method '{meth}' missing from {router_prefix}-Router's contract."
                )

    def simulate_and_assert(
        self,
        approval_args_strat_type: Type[ABIStrategy],
        clear_args_strat_type_or_inputs: Type[ABIStrategy]
        | list[Sequence[PyTypes]]
        | None,
        approval_abi_args_mod: ABIArgsMod | None,
        version: int,
        method_configs: ABICallConfigs,
        *,
        assemble_constants: bool = False,
        optimize: OptimizeOptions | None = None,
        num_dryruns: int = 1,
        txn_params: TxParams | None = None,
        model_version: int | None = None,
        model_assemble_constants: bool = False,
        model_optimize: OptimizeOptions | None = None,
        msg: str = "",
        omit_approval_call: bool = False,
        omit_clear_call: bool = False,
        executor_validation: bool = True,
        skip_validation: bool = False,
    ) -> RouterSimulationResults:
        assert not (
            omit_approval_call and omit_clear_call
        ), "Aborting and failing as all tests are being omitted"

        # --- setup local functions including reporter and stats. Also declare closure vars --- #

        # for purposes of clarity, declare all the variables for closures before each function:
        approve_sim: Simulation | None  # required for return RouterResults

        # msg4simulate:

        # msg - cf. parameters
        approval_strat: ABICallStrategy | None
        meth_name: str | None  # simulate_approval's closure as well
        call_cfg: CallConfig | None
        is_app_create: bool
        stats: dict[str, int | str] = defaultdict(int)

        def msg4simulate() -> str:
            return f"""user provide message={msg}
call_strat={type(approval_strat)}
{meth_name=}
{oc=}
{call_cfg=}
{is_app_create=}
{len(self.predicates[meth_name])=}
{stats["method_combo_count"]=}
{stats["dryrun_count"]=}
{stats["assertions_count"]=}
"""

        # update_stats:
        # num_dryruns - cf. parameters
        # stats - cf. above
        def update_stats(meth, num_preds):
            stats[str(meth)] += num_dryruns
            stats["method_combo_count"] += 1
            stats["dryrun_count"] += num_dryruns
            stats["assertions_count"] += num_dryruns * num_preds

        # simulate_approval:
        # txn_params - cf. parameters
        oc: OnComplete
        # approval_strat - cf. above

        def simulate_approval(on_create):
            tp: TxParams = deepcopy(txn_params)
            tp.update_fields(TxParams.for_app(is_app_create=on_create, on_complete=oc))
            sim_results = approve_sim.run_and_assert(
                approval_strat, txn_params=tp, msg=msg4simulate()
            )
            assert sim_results.succeeded
            if meth_name not in self.results:
                self.results[meth_name] = {}
            self.results[meth_name][(on_create, oc)] = sim_results
            update_stats(meth_name, len(self.predicates[meth_name]))

        # --- Compile Programs --- #
        approval_teal, clear_teal, contract = self.router.compile_program(
            version=version, assemble_constants=assemble_constants, optimize=optimize
        )

        model_approval_teal: str | None = None
        model_clear_teal: str | None = None
        model_contract: sdk_abi.Contract | None = None
        if self.model_router:
            (
                model_approval_teal,
                model_clear_teal,
                model_contract,
            ) = self.model_router.compile_program(
                version=cast(int, model_version),
                assemble_constants=model_assemble_constants,
                optimize=model_optimize,
            )

        if not skip_validation:
            self._validate_simulation(
                approval_args_strat_type,
                clear_args_strat_type_or_inputs,
                approval_abi_args_mod,
                num_dryruns,
                txn_params,
                model_version,
                method_configs,
                contract,
                model_contract,
                omit_clear_call,
            )

        if not txn_params:
            txn_params = TxParams()

        stats["name"] = self.router.name

        # ---- APPROVAL PROGRAM SIMULATION ---- #
        if not omit_approval_call:
            approval_strat = ABICallStrategy(
                json.dumps(contract.dictify()),
                approval_args_strat_type,
                num_dryruns=num_dryruns,
                abi_args_mod=approval_abi_args_mod,
            )
            double_check_at_least_one_method = False
            for meth_name, meth_cfg in method_configs.items():
                sig = approval_strat.method_signature(meth_name)
                approve_sim = Simulation(
                    self.algod,
                    ExecutionMode.Application,
                    approval_teal,
                    self.predicates[meth_name],
                    abi_method_signature=sig,
                    identities_teal=model_approval_teal,
                    validation=executor_validation,
                )

                for oc_str, call_cfg in asdict(meth_cfg).items():
                    oc = as_on_complete(oc_str)

                    # weird walrus is_app_create := ... to fill closure of msg4simulate()
                    if cast(CallConfig, call_cfg) & CallConfig.CALL:
                        double_check_at_least_one_method = True
                        simulate_approval(is_app_create := False)

                    if cast(CallConfig, call_cfg) & CallConfig.CREATE:
                        double_check_at_least_one_method = True
                        simulate_approval(is_app_create := True)
            assert double_check_at_least_one_method, "no method was simulated"

        # ---- CLEAR PROGRAM SIMULATION ---- #
        approval_strat = None
        call_cfg = None
        approve_sim = None
        clear_strat_or_inputs: InputStrategy  # CallStrategy | Iterable[Sequence[PyTypes]]
        clear_sim: Simulation | None = None
        if not omit_clear_call:
            assert clear_args_strat_type_or_inputs  # therefore Type[ABIStrategy] | list[Sequence[PyTypes]]
            if isinstance(clear_args_strat_type_or_inputs, list):
                clear_strat_or_inputs = cast(
                    list[Sequence[PyTypes]], clear_args_strat_type_or_inputs
                )
                # for the closure of local update_stats():
                num_dryruns = len(clear_strat_or_inputs)
            else:
                clear_strat_or_inputs = RandomArgLengthCallStrategy(
                    cast(Type[ABIStrategy], clear_args_strat_type_or_inputs),
                    max_args=2,
                    num_dryruns=num_dryruns,
                    min_args=0,
                    type_for_args=sdk_abi.ABIType.from_string("byte[8]"),
                )

            meth_name = CLEAR_STATE_CALL
            is_app_create = False
            oc = OnComplete.ClearStateOC
            clear_sim = Simulation(
                self.algod,
                ExecutionMode.Application,
                clear_teal,
                self.predicates[meth_name],
                identities_teal=model_clear_teal,
                validation=executor_validation,
            )

            sim_results = clear_sim.run_and_assert(
                clear_strat_or_inputs, msg=msg4simulate()
            )
            assert sim_results.succeeded
            if meth_name not in self.results:
                self.results[meth_name] = {}
            self.results[meth_name][(is_app_create, oc)] = sim_results
            update_stats(meth_name, len(self.predicates[meth_name]))

        # ---- Summary Statistics ---- #
        return RouterSimulationResults(
            stats=stats,
            results=self.results,
            approval_simulator=approve_sim,
            clear_simulator=clear_sim,
        )
