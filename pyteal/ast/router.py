from contextlib import contextmanager
from dataclasses import astuple, dataclass, field
from enum import IntFlag
from typing import Callable, Final, Optional, cast

from algosdk import abi as sdk_abi
from algosdk import encoding
from algosdk.v2client.algod import AlgodClient

from pyteal.ast import abi
from pyteal.ast.app import OnComplete
from pyteal.ast.assert_ import Assert
from pyteal.ast.cond import Cond
from pyteal.ast.expr import Expr
from pyteal.ast.frame import FrameVar, Proto, ProtoStackLayout
from pyteal.ast.int import EnumInt, Int
from pyteal.ast.methodsig import MethodSignature
from pyteal.ast.naryexpr import And, Or
from pyteal.ast.return_ import Approve, Reject
from pyteal.ast.scratch import ScratchSlot
from pyteal.ast.seq import Seq
from pyteal.ast.subroutine import (
    ABIReturnSubroutine,
    OutputKwArgInfo,
    Subroutine,
    SubroutineCall,
    SubroutineDefinition,
    SubroutineFnWrapper,
)
from pyteal.ast.txn import Txn
from pyteal.compiler.compiler import DEFAULT_TEAL_VERSION, Compilation, OptimizeOptions
from pyteal.compiler.sourcemap import PyTealSourceMap, _PyTealSourceMapper
from pyteal.config import METHOD_ARG_NUM_CUTOFF
from pyteal.errors import AlgodClientError, TealInputError, TealInternalError
from pyteal.ir.ops import Mode
from pyteal.stack_frame import NatalStackFrame
from pyteal.types import TealType
from pyteal.util import algod_with_assertion

ActionType = Expr | SubroutineFnWrapper | ABIReturnSubroutine


class CallConfig(IntFlag):
    """
    CallConfig: a "bitset"-like class for more fine-grained control over
    `call or create` for a method about an OnComplete case.

    This enumeration class allows for specifying one of the four following cases:
    - CALL
    - CREATE
    - ALL
    - NEVER
    for a method call on one on_complete case.
    """

    NEVER = 0
    CALL = 1
    CREATE = 2
    ALL = 3

    def approval_condition_under_config(self) -> Expr | int:
        match self:
            case CallConfig.NEVER:
                return 0
            case CallConfig.CALL:
                return Txn.application_id() != Int(0)
            case CallConfig.CREATE:
                return Txn.application_id() == Int(0)
            case CallConfig.ALL:
                return 1
            case _:
                raise TealInternalError(f"unexpected CallConfig {self}")


CallConfig.__module__ = "pyteal"


@dataclass(frozen=True)
class MethodConfig:
    """
    MethodConfig keep track of one method's CallConfigs for all OnComplete cases.

    The `MethodConfig` implementation generalized contract method call such that the registered
    method call is paired with certain OnCompletion conditions and creation conditions.
    """

    no_op: CallConfig = field(kw_only=True, default=CallConfig.NEVER)
    opt_in: CallConfig = field(kw_only=True, default=CallConfig.NEVER)
    close_out: CallConfig = field(kw_only=True, default=CallConfig.NEVER)
    clear_state: CallConfig = field(kw_only=True, default=CallConfig.NEVER)
    update_application: CallConfig = field(kw_only=True, default=CallConfig.NEVER)
    delete_application: CallConfig = field(kw_only=True, default=CallConfig.NEVER)

    def __post_init__(self):
        if self.clear_state != CallConfig.NEVER:
            raise TealInputError(
                "Attempt to construct clear state program from MethodConfig: "
                "Use Router top level argument `clear_state` instead. "
                "For more details please refer to "
                "https://pyteal.readthedocs.io/en/latest/abi.html#registering-bare-app-calls"
            )

    def is_never(self) -> bool:
        return all(map(lambda cc: cc == CallConfig.NEVER, astuple(self)))

    def approval_cond(self) -> Expr | int:
        config_oc_pairs: list[tuple[CallConfig, EnumInt]] = [
            (self.no_op, OnComplete.NoOp),
            (self.opt_in, OnComplete.OptIn),
            (self.close_out, OnComplete.CloseOut),
            (self.update_application, OnComplete.UpdateApplication),
            (self.delete_application, OnComplete.DeleteApplication),
        ]
        if all(config == CallConfig.NEVER for config, _ in config_oc_pairs):
            return 0
        elif all(config == CallConfig.ALL for config, _ in config_oc_pairs):
            return 1
        else:
            cond_list = []
            for config, oc in config_oc_pairs:
                config_cond = config.approval_condition_under_config()
                match config_cond:
                    case Expr():
                        cond_list.append(And(Txn.on_completion() == oc, config_cond))
                    case 1:
                        cond_list.append(Txn.on_completion() == oc)
                    case 0:
                        continue
                    case _:
                        raise TealInternalError(
                            f"unexpected condition_under_config: {config_cond}"
                        )
            return Or(*cond_list)


MethodConfig.__module__ = "pyteal"


@dataclass
class OnCompleteAction:
    """
    OnComplete Action, registers bare calls to one single OnCompletion case.
    """

    action: ActionType | None = field(kw_only=True, default=None)
    call_config: CallConfig = field(kw_only=True, default=CallConfig.NEVER)

    def __post_init__(self):
        if bool(self.call_config) ^ bool(self.action):
            raise TealInputError(
                f"action {self.action} and call_config {self.call_config!r} contradicts"
            )
        self.stack_frames: NatalStackFrame = NatalStackFrame()

    @staticmethod
    def never() -> "OnCompleteAction":
        return OnCompleteAction()

    @staticmethod
    def create_only(f: ActionType) -> "OnCompleteAction":
        return OnCompleteAction(action=f, call_config=CallConfig.CREATE)

    @staticmethod
    def call_only(f: ActionType) -> "OnCompleteAction":
        return OnCompleteAction(action=f, call_config=CallConfig.CALL)

    @staticmethod
    def always(f: ActionType) -> "OnCompleteAction":
        return OnCompleteAction(action=f, call_config=CallConfig.ALL)

    def is_empty(self) -> bool:
        return not self.action and self.call_config == CallConfig.NEVER


OnCompleteAction.__module__ = "pyteal"


class BareCallActions:
    """
    BareCallActions keep track of bare-call registrations to all OnCompletion cases.
    """

    def __init__(
        self,
        *,
        close_out: OnCompleteAction = OnCompleteAction.never(),
        clear_state: OnCompleteAction = OnCompleteAction.never(),
        delete_application: OnCompleteAction = OnCompleteAction.never(),
        no_op: OnCompleteAction = OnCompleteAction.never(),
        opt_in: OnCompleteAction = OnCompleteAction.never(),
        update_application: OnCompleteAction = OnCompleteAction.never(),
    ):
        self.close_out: Final[OnCompleteAction] = close_out
        self.clear_state: Final[OnCompleteAction] = clear_state
        self.delete_application: Final[OnCompleteAction] = delete_application
        self.no_op: Final[OnCompleteAction] = no_op
        self.opt_in: Final[OnCompleteAction] = opt_in
        self.update_application: Final[OnCompleteAction] = update_application
        if not self.clear_state.is_empty():
            raise TealInputError(
                "Attempt to construct clear state program from bare app call: "
                "Use Router top level argument `clear_state` instead. "
                "For more details please refer to "
                "https://pyteal.readthedocs.io/en/latest/abi.html#registering-bare-app-calls"
            )

        self.stack_frames: NatalStackFrame = NatalStackFrame()

    def asdict(self) -> dict[str, OnCompleteAction]:
        return {
            "clear_state": self.clear_state,
            "close_out": self.close_out,
            "delete_application": self.delete_application,
            "no_op": self.no_op,
            "opt_in": self.opt_in,
            "update_application": self.update_application,
        }

    def aslist(self) -> list[OnCompleteAction]:
        return list(self.asdict().values())

    def is_empty(self) -> bool:
        return all([a.is_empty() for a in self.aslist()])

    def approval_construction(self) -> Optional[Expr]:
        oc_action_pair: list[tuple[EnumInt, OnCompleteAction]] = [
            (OnComplete.NoOp, self.no_op),
            (OnComplete.OptIn, self.opt_in),
            (OnComplete.CloseOut, self.close_out),
            (OnComplete.UpdateApplication, self.update_application),
            (OnComplete.DeleteApplication, self.delete_application),
        ]
        if all(oca.is_empty() for _, oca in oc_action_pair):
            return None

        conditions_n_branches: list[CondNode] = list()
        for oc, oca in oc_action_pair:
            if oca.is_empty():
                continue
            wrapped_handler = ASTBuilder.wrap_handler(
                False, cast(ActionType, oca.action)
            )
            match oca.call_config:
                case CallConfig.ALL:
                    cond_body = wrapped_handler
                case CallConfig.CALL | CallConfig.CREATE:
                    cond_body = Seq(
                        Assert(
                            cast(
                                Expr, oca.call_config.approval_condition_under_config()
                            )
                        ),
                        wrapped_handler,
                    )
                case _:
                    raise TealInternalError(
                        f"Unexpected CallConfig: {oca.call_config!r}"
                    )
            cn = CondNode(Txn.on_completion() == oc, cond_body)
            cn.reframe_asts(oca.stack_frames)
            conditions_n_branches.append(cn)
        cond = Cond(*[[n.condition, n.branch] for n in conditions_n_branches])
        cond.stack_frames = self.stack_frames
        return cond

    def get_method_config(self) -> MethodConfig:
        return MethodConfig(
            no_op=self.no_op.call_config,
            opt_in=self.opt_in.call_config,
            close_out=self.close_out.call_config,
            update_application=self.update_application.call_config,
            delete_application=self.delete_application.call_config,
        )


BareCallActions.__module__ = "pyteal"


@dataclass(frozen=True)
class CondNode:
    """CondNode is a node inside generated program AST.

    `condition` is the logic condition that decides if the program should execute the branch.
    `branch` is the expression containing most of executation.
    """

    condition: Expr
    branch: Expr

    def reframe_asts(self, stack_frames: NatalStackFrame) -> None:
        """
        The purpose of reframe_asts is to source map the router generated ASTs to the
        current method signature, as opposed to an obtuse mapping to the router itself.
        It achieves this by traversing the AST's of `condition` and `branch` and re-setting
        their stack frames to the provided `stack_frames` belonging to the method declaration.
        """
        stack_frames.reframe(self.condition, self.branch)


CondNode.__module__ = "pyteal"


@dataclass(frozen=True)
class CondWithMethod:
    """CondWithMethod converts method_signature, condition, and method `ABIReturnSubroutine` into an AST node (`CondNode`).

    `method_signature` and `condition` generates the condition expression in `CondNode`:
    - `method_sig: str` is the method signature of `method: ABIReturnSubroutine`.
    - `condition: Expr | int` is the condition representing the `OnComplete` allowance condition,
       generated by `MethodConfig.approval_cond`:
       - `Expr`: some of `OnComplete` options are allowed, e.g.,
         `Or(Txn.on_completion() == OnComplete.NoOp, Txn.on_completion() == OnComplete.OptIn)`.
       - 1: all of `OnComplete` options for approval program are allowed
       - 0: no `OnComplete` option is allowed
         NOTE: since this is generating a dead branch in TEAL generated code, we error here on encountering a 0 condition.

    `method`, which is an `ABIReturnSubroutine`, is wrapped into an `Expr`:
    - Router would generate the code that handles IO for the subroutine:
      - Generated code parses `Txn.application_args`, converts them into ABI value instances, and passes them into method.
      - Generated code logs method result, and exit program with `Approve()`.

    Because of the introduction of `frame_pointer`, there are 2 flavors of generated code:
    - pre-frame-pointer (scratch slot based)
    - frame-pointer based.

    For more details, refer to implementation of `ASTBuilder.wrap_handler`.
    """

    method_sig: str
    condition: Expr | int
    method: ABIReturnSubroutine

    def to_cond_node(self, use_frame_pt: bool = False) -> CondNode:
        walk_in_cond = Txn.application_args[0] == MethodSignature(self.method_sig)

        if not (isinstance(self.condition, Expr) or self.condition == 1):
            raise TealInputError("Invalid condition input for CondWithMethod")

        user_frames_holder: list[NatalStackFrame] = []
        res = ASTBuilder.wrap_handler(
            True,
            self.method,
            use_frame_pt=use_frame_pt,
            handler_stack_frames_container=user_frames_holder,
        )
        assert (
            ufhlen := len(user_frames_holder)
        ) == 1, f"Unexpected length for user_frames_holder: {ufhlen}"
        user_frames: NatalStackFrame = user_frames_holder[0]

        if isinstance(self.condition, Expr):
            res = Seq(Assert(self.condition), res)

        cn = CondNode(walk_in_cond, res)
        cn.reframe_asts(user_frames)
        return cn


CondWithMethod.__module__ = "pyteal"


@dataclass
class ASTBuilder:
    def __init__(self):
        self.methods_with_conds: list[CondWithMethod] = []
        self.bare_calls: list[CondNode] = []

    def _clean_bare_calls(self) -> None:
        self.bare_calls = []

    @staticmethod
    def __filter_invalid_handlers_and_typecast(
        subroutine: ABIReturnSubroutine | SubroutineFnWrapper | Expr,
    ) -> ABIReturnSubroutine:
        """This method filters out invalid handlers that might be normal subroutine, Expr, or unroutable ABIReturnSubroutine.
        It accepts only routable ABIReturnSubroutine, and shrink the type to ABIReturnSubroutine from argument's union type.
        """
        if not isinstance(subroutine, ABIReturnSubroutine):
            raise TealInputError(
                f"method call should be only registering ABIReturnSubroutine, got {type(subroutine)}."
            )
        if not subroutine.is_abi_routable():
            raise TealInputError(
                f"method call ABIReturnSubroutine is not routable: "
                f"got {subroutine.subroutine.argument_count()} args "
                f"with {len(subroutine.subroutine.abi_args)} ABI args."
            )
        return subroutine

    @staticmethod
    def __subroutine_argument_instance_generate(
        subroutine: ABIReturnSubroutine,
    ) -> tuple[list[abi.BaseType], list[abi.BaseType], list[abi.Transaction]]:
        # All subroutine args types
        type_specs = cast(list[abi.TypeSpec], subroutine.subroutine.expected_arg_types)

        # All subroutine arg values, initialize here and use below instead of
        # creating new instances on the fly, so we don't have to think about splicing
        # back in the transaction types
        arg_vals = [typespec.new_instance() for typespec in type_specs]

        # Only args that appear in app args
        app_arg_vals: list[abi.BaseType] = [
            ats for ats in arg_vals if not isinstance(ats, abi.Transaction)
        ]

        # only transaction args (these are omitted from app args)
        txn_arg_vals: list[abi.Transaction] = [
            ats for ats in arg_vals if isinstance(ats, abi.Transaction)
        ]

        for aav in app_arg_vals:
            # If we're here we know the top level isn't a Transaction but a transaction may
            # be included in some collection type like a Tuple or Array, raise error
            # as these are not supported
            if abi.contains_type_spec(aav.type_spec(), abi.TransactionTypeSpecs):
                raise TealInputError(
                    "A Transaction type may not be included in Tuples or Arrays"
                )

        return arg_vals, app_arg_vals, txn_arg_vals

    @staticmethod
    def __decode_constructions_and_args(
        arg_vals: list[abi.BaseType],
        app_arg_vals: list[abi.BaseType],
        txn_arg_vals: list[abi.Transaction],
        subroutine: ABIReturnSubroutine,
        use_frame_pt: bool = False,
    ) -> tuple[list[Expr], list[abi.BaseType], Optional[Proto]]:
        """
        Assumption: arg_vals = app_args_vals union with txn_arg_vals
        """

        # if subroutine has ABI output, then local variables start from 1
        # otherwise local variables start from 0
        index_start_from = 0 if subroutine.output_kwarg_info is None else 1

        # prepare the local stack type list for local variable allocation
        local_types: list[TealType] = [i._stored_value.storage_type() for i in arg_vals]

        if subroutine.output_kwarg_info:
            local_types = [
                subroutine.output_kwarg_info.abi_type.storage_type()
            ] + local_types

        # assign to a var here since we modify app_arg_vals later
        tuplify = len(app_arg_vals) > METHOD_ARG_NUM_CUTOFF

        # Tuple-ify any app args after the limit
        tupled_app_args: list[abi.BaseType] = []

        if tuplify:
            tupled_app_args = app_arg_vals[METHOD_ARG_NUM_CUTOFF - 1 :]
            last_arg_specs_grouped: list[abi.TypeSpec] = [
                t.type_spec() for t in tupled_app_args
            ]
            app_arg_vals = app_arg_vals[: METHOD_ARG_NUM_CUTOFF - 1]
            app_args_tupled = abi.TupleTypeSpec(*last_arg_specs_grouped).new_instance()
            local_types.append(app_args_tupled._stored_value.storage_type())
            app_arg_vals.append(app_args_tupled)

        proto: Optional[Proto] = None
        if use_frame_pt:
            proto = Proto(0, 0, mem_layout=ProtoStackLayout([], local_types, 0))
            for i, arg_val in enumerate(arg_vals):
                arg_val._stored_value = FrameVar(proto, i + index_start_from)
            if tuplify:
                app_arg_vals[-1]._stored_value = FrameVar(proto, len(local_types) - 1)

        # decode app args
        decode_instructions: list[Expr] = [
            app_arg.decode(Txn.application_args[idx + 1])
            for idx, app_arg in enumerate(app_arg_vals)
        ]

        # "decode" transaction types by setting the relative index
        if len(txn_arg_vals) > 0:
            txn_arg_len = len(txn_arg_vals)
            # The transactions should appear in the group in the order they're specified in the method signature
            # and should be relative to the current transaction.

            # ex:
            # doit(axfer,pay,appl)
            # would be 4 transactions
            #      current_idx-3 = axfer
            #      current_idx-2 = pay
            #      current_idx-1 = appl
            #      current_idx-0 = the txn that triggered the current eval (not specified but here for completeness)

            # since we're iterating in order of the txns appearance in the args we
            # subtract the current index from the total length to get the offset.
            # and subtract that from the current index to get the absolute position
            # in the group

            txn_decode_instructions: list[Expr] = []

            for idx, arg_val in enumerate(txn_arg_vals):
                txn_decode_instructions.append(
                    arg_val._set_index(Txn.group_index() - Int(txn_arg_len - idx))
                )
                spec = arg_val.type_spec()
                if type(spec) is not abi.TransactionTypeSpec:
                    # this is a specific transaction type
                    txn_decode_instructions.append(
                        Assert(arg_val.get().type_enum() == spec.txn_type_enum())
                    )

            decode_instructions += txn_decode_instructions

        # de-tuple into specific values using `store_into` on
        # each element of the tuple'd arguments
        if tuplify:
            tupled_arg: abi.Tuple = cast(abi.Tuple, app_arg_vals[-1])
            de_tuple_instructions: list[Expr] = [
                tupled_arg[idx].store_into(arg_val)
                for idx, arg_val in enumerate(tupled_app_args)
            ]
            decode_instructions += de_tuple_instructions

        return decode_instructions, arg_vals, proto

    @staticmethod
    def wrap_handler(
        is_method_call: bool,
        handler: ActionType,
        *,
        wrap_to_name: str | None = None,
        use_frame_pt: bool = False,
        handler_stack_frames_container: list[NatalStackFrame] | None = None,
    ) -> Expr:
        """This is a helper function that handles transaction arguments passing in bare-app-call/abi-method handlers.
        If `is_method_call` is True, then it can only be `ABIReturnSubroutine`,
        otherwise:
            - both `ABIReturnSubroutine` and `Subroutine` takes 0 argument on the stack.
            - all three cases have none (or void) type.
        On ABI method case, if the ABI method has more than 15 args, this function manages to de-tuple
        the last (16-th) Txn app-arg into a list of ABI method arguments, and pass in to the ABI method.
        Args:
            is_method_call: a boolean value that specify if the handler is an ABI method.
            handler: an `ABIReturnSubroutine`, or `SubroutineFnWrapper` (for `Subroutine` case), or an `Expr`.
            use_frame_pt: a boolean value that specify if router is compiled to frame pointer based code.
            handler_stack_frames_container: an optional list that is filled with NatalStackFrame's
                used in source mapping.
        Returns:
            Expr:
                - for bare-appcall it returns an expression that the handler takes no txn arg and Approve
                - for abi-method it returns the txn args correctly decomposed into ABI variables,
                  passed in ABIReturnSubroutine and logged, then approve.
        """

        def scavenge(frames_holder) -> None:
            """
            Scavenges the stack frames from a given `frames_holder` and appends them to the
            source mapping output variable `handler_stack_frames_container`.
            """
            if handler_stack_frames_container is not None:
                handler_stack_frames_container.append(frames_holder.stack_frames)

        handler_evald: abi.ReturnedValue | SubroutineCall

        if not is_method_call:
            wrap_to_name = wrap_to_name or "bare appcall"

            match handler:
                case Expr():
                    if handler.type_of() != TealType.none:
                        raise TealInputError(
                            f"{wrap_to_name} handler should be TealType.none not {handler.type_of()}."
                        )
                    scavenge(handler)
                    return handler if handler.has_return() else Seq(handler, Approve())
                case SubroutineFnWrapper():
                    if handler.type_of() != TealType.none:
                        raise TealInputError(
                            f"subroutine call should be returning TealType.none not {handler.type_of()}."
                        )
                    if handler.subroutine.argument_count() != 0:
                        raise TealInputError(
                            f"subroutine call should take 0 arg for {wrap_to_name}. "
                            f"this subroutine takes {handler.subroutine.argument_count()}."
                        )
                    handler_evald = handler()
                    if isinstance(handler_evald, abi.ReturnedValue):
                        handler_evald = handler_evald.computation
                    scavenge(cast(SubroutineCall, handler_evald).subroutine)
                    return Seq(handler_evald, Approve())
                case ABIReturnSubroutine():
                    if handler.type_of() != "void":
                        raise TealInputError(
                            f"abi-returning subroutine call should be returning void not {handler.type_of()}."
                        )
                    if handler.subroutine.argument_count() != 0:
                        raise TealInputError(
                            f"abi-returning subroutine call should take 0 arg for {wrap_to_name}. "
                            f"this abi-returning subroutine takes {handler.subroutine.argument_count()}."
                        )
                    handler_evald = handler()
                    if isinstance(handler_evald, abi.ReturnedValue):
                        handler_evald = handler_evald.computation

                    scavenge(handler_evald)
                    return Seq(cast(Expr, handler_evald), Approve())
                case _:
                    raise TealInputError(
                        f"{wrap_to_name} can only accept: none type Expr, or Subroutine/ABIReturnSubroutine with none return and no arg"
                    )

        # else: method case
        wrap_to_name = wrap_to_name or "method call"
        if not isinstance(handler, ABIReturnSubroutine):
            raise TealInputError(
                f"{wrap_to_name} should be only registering ABIReturnSubroutine, got {type(handler)}."
            )
        if not handler.is_abi_routable():
            raise TealInputError(
                f"{wrap_to_name} ABIReturnSubroutine is not routable "
                f"got {handler.subroutine.argument_count()} args with {len(handler.subroutine.abi_args)} ABI args."
            )

        ret_expr, subdef = (
            ASTBuilder.__de_abify_subroutine_frame_pointers(handler)
            if use_frame_pt
            else ASTBuilder.__de_abify_subroutine_vanilla(handler)
        )
        scavenge(subdef)
        return ret_expr

    @staticmethod
    def __de_abify_subroutine_vanilla(
        handler: ActionType,
    ) -> tuple[Expr, SubroutineDefinition]:
        """This private function retains the previous (pre-frame-pointer) logic of handling ABIReturnSubroutine method's IO.

        This function can be roughly separated into following 4 parts:
        - handler type check
        - handler argument instance generate
        - handler argument decode from Txn.application_args
        - generating execution branch that calls handler and handles handler return.
          NOTE: the very last step is handled differently from the frame pointer version; see the illustration below:

        |
        | main execution
        |
        `-> (assuming satisfying all preconditions: method selector match + OnComplete options match)
            +-----------------------------------------------------------------------------------+
            | We need to first allocate some scratch slots for the handler's ABI arguments,     |
            | for we don't want the intermediate handler steps to destroy memory on arguments.  |
            |                                                                                   |
            | Decoding scheme relies on internal storage in ABI value (default scratch slot).   |
            | NOTE: if the handler has more than 15 args, we need to de-tuple the last one.     |
            |       The detupling process is also done over the scratch slots.                  |
            |                                                                                   |
            | This section represents the expressions in `decoding_steps`.                      |
            +-----------------------------------------------------------------------------------+
            | At this point, all of the handler arguments (ABI typed) are prepared.             |
            | We call the handler with all these handler arguments.                             |
            | If the handler has output, we dig the result to top of the stack and log it.      |
            |                                                                                   |
            | NOTE: if output exists inside of a subroutine, we alloc a scratch slot for output.|
            |       Right before retsub, use `deferred_expr` to place output encoding on stack. |
            +-----------------------------------------------------------------------------------+
            | Now that the handler return (if exists) is handled, we `Approve()` and exit prog. |
            +-----------------------------------------------------------------------------------+
        """
        handler = ASTBuilder.__filter_invalid_handlers_and_typecast(handler)
        (
            arg_vals,
            app_arg_vals,
            txn_arg_vals,
        ) = ASTBuilder.__subroutine_argument_instance_generate(handler)

        (
            decode_instructions,
            arg_vals,
            _,
        ) = ASTBuilder.__decode_constructions_and_args(
            arg_vals, app_arg_vals, txn_arg_vals, handler
        )

        ret_expr: Expr
        handler_evald: abi.ReturnedValue | SubroutineCall
        if handler.type_of() == sdk_abi.Returns.VOID:
            ret_expr = Seq(
                *decode_instructions,
                cast(SubroutineCall, handler_evald := handler(*arg_vals)),
                Approve(),
            )
        else:
            output_temp: abi.BaseType = cast(
                OutputKwArgInfo, handler.output_kwarg_info
            ).abi_type.new_instance()
            handler_evald = cast(abi.ReturnedValue, handler(*arg_vals))
            ret_expr = Seq(
                *decode_instructions,
                handler_evald.store_into(output_temp),
                abi.MethodReturn(output_temp),
                Approve(),
            )

        if isinstance(handler_evald, abi.ReturnedValue):
            handler_evald = handler_evald.computation

        return ret_expr, cast(SubroutineCall, handler_evald).subroutine

    @staticmethod
    def __de_abify_subroutine_frame_pointers(
        handler: ActionType,
    ) -> tuple[Expr, SubroutineDefinition]:
        """This private function implements the frame-pointer-based logic of handling ABIReturnSubroutine method's IO.

        This function can be roughly separated into following 4 parts:
        - handler type check
        - handler argument instance generate
        - handler argument decode from Txn.application_args (with use_frame_pt=True option on)
        - generating execution branch that calls the handler and handles handler return.
          NOTE: the very last step is handled differently from the frame pointer version; see the illustration below:

        |
        | main execution
        |
        `-> (assuming satisfying all preconditions: method selector match + OnComplete options match)
            +-----------------------------------------------------------------------------------+
            | We wrap the following section up in an intermediate function:                     |
            +-----------------------------------------------------------------------------------+
            |                                                                                   |
            |  We construct an intermediate subroutine with 0 args and 0 returns as follows:    |
            |  +--------------------------------------------------------------------------------+
            |  | Thus we use `proto 0 0` to clean up stack once handler computation completes.  |
            |  +--------------------------------------------------------------------------------+
            |  |We need to allocate some stack space to handle memory for the following 2 cases:|
            |  | - If handler has an ABI output returning, need to store in a grid on stack.    |
            |  | - All of the other handler arguments from `Txn.application_args` should be     |
            |  |   decoded into ABI values and placed on stack.                                 |
            |  |   NOTE: if the handler has more than 15 args, we need to de-tuple the last one.|
            |  |         The detupling process is also done over the stack with frame pointers. |
            |  |                                                                                |
            |  | To keep track of each arg's memory location,                                   |
            |  | we use FrameVar to keep track of relative dist against stack height at proto.  |
            |  |                                                                                |
            |  | Also notice that all of the decoding operations are done over local vars,      |
            |  | proto 0 0 can come in and clean all the stack variables away.                  |
            |  |                                                                                |
            |  | This section represents the expressions in `decoding_steps`.                   |
            |  +--------------------------------------------------------------------------------+
            |  | At this point, all of the handler arguments (ABI typed) are prepared.          |
            |  | We call the handler with all of these handler arguments.                       |
            |  | If the handler has output, we dig the result to the top of stack and log it.   |
            |  |                                                                                |
            |  | This section represents the expressions in `returning_steps`.                  |
            +  +--------------------------------------------------------------------------------+
            |                                                                                   |
            | Now that handler is done computing in the intermediate function,                  |
            | we `Approve()` and exit prog.                                                     |
            +-----------------------------------------------------------------------------------+
        """
        handler = ASTBuilder.__filter_invalid_handlers_and_typecast(handler)
        (
            arg_vals,
            app_arg_vals,
            txn_arg_vals,
        ) = ASTBuilder.__subroutine_argument_instance_generate(handler)

        (
            decode_instructions,
            arg_vals,
            proto,
        ) = ASTBuilder.__decode_constructions_and_args(
            arg_vals,
            app_arg_vals,
            txn_arg_vals,
            handler,
            use_frame_pt=True,
        )

        subroutine_caster = Subroutine(TealType.none, f"{handler.name()}_caster")

        proto = cast(Proto, proto)
        proto.mem_layout = cast(ProtoStackLayout, proto.mem_layout)

        decoding_steps: list[Expr] = [
            *proto.mem_layout._succinct_repr(),
            *decode_instructions,
        ]
        returning_steps: list[Expr]

        handler_evald: abi.ReturnedValue | SubroutineCall
        if handler.type_of() == sdk_abi.Returns.VOID:
            returning_steps = [cast(Expr, handler_evald := handler(*arg_vals))]
        else:
            output_temp: abi.BaseType = cast(
                OutputKwArgInfo, handler.output_kwarg_info
            ).abi_type.new_instance()
            output_temp._stored_value = FrameVar(proto, 0)
            returned_val: abi.ReturnedValue = cast(
                abi.ReturnedValue, handler_evald := handler(*arg_vals)
            )
            returning_steps = [
                returned_val.store_into(output_temp),
                abi.MethodReturn(output_temp),
            ]

        def declaration():
            return Seq(*decoding_steps, *returning_steps)

        if isinstance(handler_evald, abi.ReturnedValue):
            handler_evald = handler_evald.computation

        return (
            Seq(subroutine_caster(declaration)(), Approve()),
            cast(SubroutineCall, handler_evald).subroutine,
        )

    def add_method_to_ast(
        self, method_signature: str, cond: Expr | int, handler: ABIReturnSubroutine
    ) -> None:
        if isinstance(cond, int) and cond == 0:
            return
        self.methods_with_conds.append(CondWithMethod(method_signature, cond, handler))

    def program_construction(self, use_frame_pt: bool = False) -> Expr:
        conditions_n_branches: list[CondNode] = self.bare_calls + [
            method_with_cond.to_cond_node(use_frame_pt=use_frame_pt)
            for method_with_cond in self.methods_with_conds
        ]

        if not conditions_n_branches:
            return Reject()
        return Cond(*[[n.condition, n.branch] for n in conditions_n_branches])


ASTBuilder.__module__ = "pyteal"


@dataclass(frozen=True)
class RouterResults:
    approval_teal: str
    clear_teal: str
    abi_contract: sdk_abi.Contract
    approval_sourcemap: Optional[PyTealSourceMap] = None
    clear_sourcemap: Optional[PyTealSourceMap] = None


RouterResults.__module__ = "pyteal"


@dataclass
class _RouterBundle:
    """Private class that includes a full sourcemapper object"""

    approval_program: Expr
    clear_program: Expr
    abi_contract: sdk_abi.Contract
    approval_teal: str
    clear_teal: str
    approval_sourcemapper: Optional[_PyTealSourceMapper] = None
    clear_sourcemapper: Optional[_PyTealSourceMapper] = None
    input: Optional["_RouterCompileInput"] = None

    def get_results(self) -> RouterResults:
        approval_sourcemap: PyTealSourceMap | None = None
        clear_sourcemap: PyTealSourceMap | None = None
        if self.approval_sourcemapper:
            approval_sourcemap = self.approval_sourcemapper.get_sourcemap(
                self.approval_teal
            )
        if self.clear_sourcemapper:
            clear_sourcemap = self.clear_sourcemapper.get_sourcemap(self.clear_teal)

        return RouterResults(
            approval_teal=self.approval_teal,
            clear_teal=self.clear_teal,
            abi_contract=self.abi_contract,
            approval_sourcemap=approval_sourcemap,
            clear_sourcemap=clear_sourcemap,
        )


@dataclass
class _RouterCompileInput:
    version: int
    assemble_constants: bool
    optimize: Optional[OptimizeOptions] = None
    with_sourcemaps: bool = False
    pcs_in_sourcemaps: bool = False
    approval_filename: Optional[str] = None
    clear_filename: Optional[str] = None
    algod_client: Optional[AlgodClient] = None
    annotate_teal: bool = False
    annotate_teal_headers: bool = False
    annotate_teal_concise: bool = True

    def __post_init__(self):
        # The following params are non-sensical when truthy without sourcemaps.
        # However, they are not defining anything actionable so are simple ignored
        # rather than erroring when `with_source == False`:
        # * pcs_in_sourcemap
        # * approval_filename
        # * clear_filename
        # * algod_client

        # On the other hand, self.annotate_teal indicates a user request which cannot
        # be provided on when there isn't a sourcemap
        if self.annotate_teal and not self.with_sourcemaps:
            raise ValueError(
                "In order annotate generated teal source, must set with_sourcemap True"
            )

        if self.pcs_in_sourcemaps:
            # bootstrap an algod_client if not provided, and in either case, run a healthcheck
            try:
                self.algod_client = algod_with_assertion(self.algod_client)
            except AlgodClientError as ace:
                raise ResourceWarning(
                    "algod_with_assertion has failed: are you sure there is an available node such as Sandbox?"
                ) from ace

    def get_compilation(self, program: Expr) -> Compilation:
        return Compilation(
            ast=program,
            mode=Mode.Application,
            version=self.version,
            assemble_constants=self.assemble_constants,
            optimize=self.optimize,
        )


class Router:
    """
    The Router class helps construct the approval and clear state programs for an ARC-4 compliant
    application.

    Additionally, this class can produce an ARC-4 contract description object for the application.

    **WARNING:** The ABI Router is still taking shape and is subject to backwards incompatible changes.

    * Based on feedback, the API and usage patterns are likely to change.
    * Expect migration issues in future PyTeal versions.

    For these reasons, we strongly recommend using :any:`pragma` to pin the version of PyTeal in your
    source code.
    """

    def __init__(
        self,
        name: str,
        bare_calls: BareCallActions | None = None,
        descr: str | None = None,
        *,
        clear_state: Optional[ActionType] = None,
    ) -> None:
        """
        Args:
            name: the name of the smart contract, used in the JSON object.
            bare_calls: the bare app call registered for each on_completion.
            descr: a description of the smart contract, used in the JSON object.
            clear_state: an expression describing the behavior of clear state program. This
                expression will be the entirety of the clear state program; no additional code is
                inserted by the Router. If not provided, the clear state program will always reject.
        """

        self.name: str = name
        self.descr = descr

        self.approval_ast = ASTBuilder()
        self.clear_state: Expr = (
            Reject()
            if clear_state is None
            else ASTBuilder.wrap_handler(
                False, clear_state, wrap_to_name="clear state call"
            )
        )

        self.methods: list[sdk_abi.Method] = []
        self.method_sig_to_selector: dict[str, bytes] = dict()
        self.method_selector_to_sig: dict[bytes, str] = dict()

        self.bare_call_actions: BareCallActions = bare_calls or BareCallActions()

        # maps method signature (or None for bare call) to MethodConfig:
        self.method_configs: dict[str | None, MethodConfig] = dict()

        if not self.bare_call_actions.is_empty():
            self.method_configs[None] = self.bare_call_actions.get_method_config()

    def _clean(self) -> None:
        self.approval_ast._clean_bare_calls()

    def add_method_handler(
        self,
        method_call: ABIReturnSubroutine,
        overriding_name: str | None = None,
        method_config: MethodConfig | None = None,
        description: str | None = None,
    ) -> ABIReturnSubroutine:
        """Add a method call handler to this Router.

        Args:
            method_call: An ABIReturnSubroutine that implements the method body.
            overriding_name (optional): A name for this method. Defaults to the function name of
                method_call.
            method_config (optional): An object describing the on completion actions and
                creation/non-creation call statuses that are valid for calling this method. All
                invalid configurations will be rejected. Defaults to :code:`MethodConfig(no_op=CallConfig.CALL)`
                (i.e. only the no-op action during a non-creation call is accepted) if none is provided.
            description (optional): A description for this method. Defaults to the docstring of
                method_call, if there is one.
        """
        if not isinstance(method_call, ABIReturnSubroutine):
            raise TealInputError(
                f"for adding method handler, must be ABIReturnSubroutine but method_call is {type(method_call)}"
            )
        method_signature = method_call.method_signature(overriding_name)
        if method_config is None:
            method_config = MethodConfig(no_op=CallConfig.CALL)
        if method_config.is_never():
            raise TealInputError(
                f"registered method {method_signature} is never executed"
            )
        method_selector = encoding.checksum(bytes(method_signature, "utf-8"))[:4]

        if method_signature in self.method_sig_to_selector:
            raise TealInputError(f"re-registering method {method_signature} detected")
        if method_selector in self.method_selector_to_sig:
            raise TealInputError(
                f"re-registering method {method_signature} has hash collision "
                f"with {self.method_selector_to_sig[method_selector]}"
            )

        meth = method_call.method_spec()
        if description is not None:
            meth.desc = description
        self.methods.append(meth)

        self.method_sig_to_selector[method_signature] = method_selector
        self.method_selector_to_sig[method_selector] = method_signature

        method_approval_cond = method_config.approval_cond()
        self.approval_ast.add_method_to_ast(
            method_signature, method_approval_cond, method_call
        )
        self.method_configs[method_signature] = method_config
        return method_call

    def method(
        self,
        func: Callable | None = None,
        /,
        *,
        name: str | None = None,
        description: str | None = None,
        no_op: CallConfig | None = None,
        opt_in: CallConfig | None = None,
        close_out: CallConfig | None = None,
        clear_state: CallConfig | None = None,
        update_application: CallConfig | None = None,
        delete_application: CallConfig | None = None,
    ):
        """This is an alternative way to register a method, as supposed to :code:`add_method_handler`.

        This is a decorator that's meant to be used over a Python function, which is internally
        wrapped with ABIReturnSubroutine. Additional keyword arguments on this decorator can be used
        to specify the OnCompletion statuses that are valid for the registered method.

        NOTE: By default, all OnCompletion actions other than `no_op` are set to `CallConfig.NEVER`,
        while `no_op` field is set to `CallConfig.CALL`. However, if you provide any keywords for
        OnCompletion actions, then the `no_op` field will default to `CallConfig.NEVER`.

        Args:
            func: A function that implements the method body. This should *NOT* be wrapped with the
                :code:`ABIReturnSubroutine` decorator yet.
            name (optional): A name for this method. Defaults to the function name of func.
            description (optional): A description for this method. Defaults to the docstring of
                func, if there is one.
            no_op (optional): The allowed calls during :code:`OnComplete.NoOp`.
            opt_in (optional): The allowed calls during :code:`OnComplete.OptIn`.
            close_out (optional): The allowed calls during :code:`OnComplete.CloseOut`.
            clear_state (optional): The allowed calls during :code:`OnComplete.ClearState`.
                This argument has been deprecated, and will error on compile time if one wants to access it.
                Use Router top level argument `clear_state` instead.
            update_application (optional): The allowed calls during :code:`OnComplete.UpdateApplication`.
            delete_application (optional): The allowed calls during :code:`OnComplete.DeleteApplication`.
        """
        # we use `is None` extensively for CallConfig to distinguish 2 following cases
        # - None
        # - CallConfig.Never
        # both cases evaluate to False in if statement.
        if clear_state is not None:
            raise TealInputError(
                "Attempt to register ABI method for clear state program: "
                "Use Router top level argument `clear_state` instead. "
                "For more details please refer to "
                "https://pyteal.readthedocs.io/en/latest/abi.html#registering-bare-app-calls"
            )

        def wrap(_func) -> ABIReturnSubroutine:
            wrapped_subroutine = ABIReturnSubroutine(_func, overriding_name=name)
            call_configs: MethodConfig

            ocs = dict(
                no_op=no_op,
                opt_in=opt_in,
                close_out=close_out,
                clear_state=clear_state,
                update_application=update_application,
                delete_application=delete_application,
            )
            if all(oc is None for oc in ocs.values()):
                call_configs = MethodConfig(no_op=CallConfig.CALL)
            else:

                def none_to_never(x: None | CallConfig):
                    return CallConfig.NEVER if x is None else x

                call_configs = MethodConfig(
                    **{k: none_to_never(v) for k, v in ocs.items()}
                )
            return self.add_method_handler(
                wrapped_subroutine, name, call_configs, description
            )

        if not func:
            return wrap
        return wrap(func)

    def contract_construct(self) -> sdk_abi.Contract:
        """A helper function in constructing a `Contract` object.

        It takes out the method spec from approval program methods,
        and constructs an `Contract` object.

        Returns:
            A Python SDK `Contract` object constructed from the registered methods on this router.
        """

        return sdk_abi.Contract(self.name, self.methods, self.descr)

    def _build_program(
        self,
        *,
        version: int = DEFAULT_TEAL_VERSION,
        optimize: OptimizeOptions | None = None,
    ) -> tuple[Expr, Expr, sdk_abi.Contract]:
        """
        Constructs ASTs for approval and clear-state programs from the registered methods and bare
        app calls in the router, and also generates a Contract object to allow client read and call
        the methods easily.

        Note that if no methods or bare app call actions have been registered to either the approval
        or clear state programs, then that program will reject all transactions.

        Returns:
            A tuple of three objects.

            * approval_program: an AST for approval program
            * clear_state_program: an AST for clear-state program
            * contract: a Python SDK Contract object to allow clients to make off-chain calls
        """
        if not self.bare_call_actions.is_empty():
            bare_call_approval = self.bare_call_actions.approval_construction()
            if bare_call_approval:
                self.approval_ast.bare_calls = [
                    CondNode(
                        cond := Txn.application_args.length() == Int(0),
                        act := cast(Expr, bare_call_approval),
                    )
                ]
                bare_call_approval.stack_frames.reframe(cond)
                act.stack_frames = bare_call_approval.stack_frames

        optimize = optimize or OptimizeOptions()
        use_frame_pt = optimize.use_frame_pointers(version)
        return (
            self.approval_ast.program_construction(use_frame_pt=use_frame_pt),
            self.clear_state,
            self.contract_construct(),
        )

    @contextmanager
    def _cleaning_context(self):
        starting_slot_id = ScratchSlot.nextSlotId
        try:
            yield
        finally:
            self._clean()
            ScratchSlot.reset_slot_numbering(starting_slot_id)

    def compile_program(
        self,
        *,
        version: int = DEFAULT_TEAL_VERSION,
        assemble_constants: bool = False,
        optimize: Optional[OptimizeOptions] = None,
    ) -> tuple[str, str, sdk_abi.Contract]:
        """
        Constructs and compiles approval and clear-state programs from the registered methods and
        bare app calls in the router, and also generates a Contract object to allow client read and call
        the methods easily.

        This method combines `Router._build_program` and `Compilation.compile`.

        Note that if no methods or bare app call actions have been registered to either the approval
        or clear state programs, then that program will reject all transactions.

        Returns:
            A tuple of three objects.

            * approval_program: compiled approval program string
            * clear_state_program: compiled clear-state program string
            * contract: a Python SDK Contract object to allow clients to make off-chain calls

        NOTE: For generating a source map, please refer to the `Router.compile` method.
        """
        input = _RouterCompileInput(
            version=version,
            assemble_constants=assemble_constants,
            optimize=optimize,
        )
        cpb = self._build_impl(input)

        return cpb.approval_teal, cpb.clear_teal, cpb.abi_contract

    def compile(
        self,
        *,
        version: int = DEFAULT_TEAL_VERSION,
        assemble_constants: bool = False,
        optimize: Optional[OptimizeOptions] = None,
        approval_filename: Optional[str] = None,
        clear_filename: Optional[str] = None,
        with_sourcemaps: bool = False,
        pcs_in_sourcemap: bool = False,
        algod_client: Optional[AlgodClient] = None,
        annotate_teal: bool = False,
        annotate_teal_headers: bool = False,
        annotate_teal_concise: bool = True,
    ) -> RouterResults:
        """
        Constructs and compiles approval and clear-state programs from the registered methods and
        bare app calls in the router, and also generates a Contract object to allow client read and call
        the methods easily.

        This method combines `Router._build_program` and `Compilation.compile`.

        Note that if no methods or bare app call actions have been registered to either the approval
        or clear state programs, then that program will reject all transactions.

        Args:
            version (optional): The TEAL version to compile to. Defaults to `DEFAULT_TEAL_VERSION`.
            assemble_constants (optional): When `True`, the compiler will assemble constants to
                intc and bytec blocks. Defaults to `False`.
            optimize (optional): An `OptimizeOptions` object to use to provide optimization information
                to the compiler.
            approval_filename (optional): The filename to use in the sourcemap for the approval program.
                If not provided, the router will use the Router object's `name` field with suffix "_approval.teal".
            clear_filename (optional): The filename to use in the sourcemap for the clear program.
                If not provided, the router will use the Router object's `name` field with suffix "_clear.teal".
            with_sourcemaps (optional): When `True`, the compiler will produce source maps that map the
                generated approval and clear TEAL program back to the original PyTeal source code.
                Defaults to `False`.
            pcs_in_sourcemap (optional): When `True`, the compiler will include the program counter in
                relevant sourcemap artifacts. This requires an `AlgodClient` (see next param).
                Defaults to `False`.
            algod_client (optional): An `AlgodClient` to use to fetch program counters. Defaults to `None`.
                When `pcs_in_sourcemap` is `True` and `algod_client` is not provided, the compiler will
                assume that an Algorand Sandbox algod client is running on the default port (4001) and -if
                this is not the case- will raise an exception.
            annotate_teal (optional): When `True`, the compiler will produce a TEAL program with comments
                that describe the PyTeal source code that generated each line of the program.
                Defaults to `False`.
            annotate_teal_headers (optional): When `True` along with `annotate_teal` being `True`, a header
                line with column names will be added at the top of the annotated teal. Defaults to `False`.
            annotate_teal_concise (optional): When `True` along with `annotate_teal` being `True`, the compiler
                will provide fewer columns in the annotated teal. Defaults to `True`.


        Returns:
            A RouterResults containing the following:
            * approval_teal (str): compiled approval program
            * clear_teal (str): compiled clear-state program
            * abi_contract (abi.Contract): a Python SDK Contract object to allow clients to make off-chain calls
            * approval_sourcemap (PyTealSourceMap | None): source map results for approval program
            * clear_sourcemap (PyTealSourceMap | None): source map results for clear-state program
        """
        approval_filename = approval_filename or f"{self.name}_approval.teal"
        clear_filename = clear_filename or f"{self.name}_clear.teal"

        input = _RouterCompileInput(
            version=version,
            assemble_constants=assemble_constants,
            optimize=optimize,
            with_sourcemaps=with_sourcemaps,
            approval_filename=approval_filename,
            clear_filename=clear_filename,
            pcs_in_sourcemaps=pcs_in_sourcemap,
            algod_client=algod_client,
            annotate_teal=annotate_teal,
            annotate_teal_headers=annotate_teal_headers,
            annotate_teal_concise=annotate_teal_concise,
        )
        return self._build_impl(input).get_results()

    def _build_impl(self, input: _RouterCompileInput) -> _RouterBundle:
        with self._cleaning_context():
            ap, csp, contract = self._build_program(
                version=input.version, optimize=input.optimize
            )

            abundle = input.get_compilation(ap)._compile_impl(
                with_sourcemap=input.with_sourcemaps,
                teal_filename=input.approval_filename,
                pcs_in_sourcemap=input.pcs_in_sourcemaps,
                algod_client=input.algod_client,
                annotate_teal=input.annotate_teal,
                annotate_teal_headers=input.annotate_teal_headers,
                annotate_teal_concise=input.annotate_teal_concise,
            )

            # TODO: ideally, the clear-state compilation ought to be in it's own
            # _cleaning_context to allow for fresh slot numbering. However,
            # the side effects of separating is not yet obvious and
            # clear state programs generally aren't so complex so this isn't
            # of high urgency
            csbundle = input.get_compilation(csp)._compile_impl(
                with_sourcemap=input.with_sourcemaps,
                teal_filename=input.clear_filename,
                pcs_in_sourcemap=input.pcs_in_sourcemaps,
                algod_client=input.algod_client,
                annotate_teal=input.annotate_teal,
                annotate_teal_headers=input.annotate_teal_headers,
                annotate_teal_concise=input.annotate_teal_concise,
            )

        return _RouterBundle(
            approval_program=ap,
            clear_program=csp,
            abi_contract=contract,
            approval_teal=abundle.teal,
            clear_teal=csbundle.teal,
            approval_sourcemapper=abundle.sourcemapper,
            clear_sourcemapper=csbundle.sourcemapper,
            input=input,
        )


Router.__module__ = "pyteal"
