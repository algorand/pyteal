from dataclasses import dataclass, field
from typing import Any, cast, Optional
from enum import Enum

import more_itertools
import algosdk.abi as sdk_abi

from pyteal.config import METHOD_ARG_NUM_LIMIT
from pyteal.errors import TealInputError
from pyteal.types import TealType
from pyteal.compiler.compiler import compileTeal, DEFAULT_TEAL_VERSION, OptimizeOptions
from pyteal.ir.ops import Mode

from pyteal.ast import abi
from pyteal.ast.subroutine import (
    OutputKwArgInfo,
    SubroutineFnWrapper,
    ABIReturnSubroutine,
)
from pyteal.ast.cond import Cond
from pyteal.ast.expr import Expr
from pyteal.ast.app import OnComplete, EnumInt
from pyteal.ast.int import Int
from pyteal.ast.seq import Seq
from pyteal.ast.methodsig import MethodSignature
from pyteal.ast.naryexpr import And, Or
from pyteal.ast.txn import Txn
from pyteal.ast.return_ import Approve


class CallConfig(Enum):
    """
    CallConfigs: a "bitset" alike class for more fine-grained control over
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

    def __or__(self, other: object) -> "CallConfig":
        if not isinstance(other, CallConfig):
            raise TealInputError("OCMethodConfig must be compared with same class")
        return CallConfig(self.value | other.value)

    def __and__(self, other: object) -> "CallConfig":
        if not isinstance(other, CallConfig):
            raise TealInputError("OCMethodConfig must be compared with same class")
        return CallConfig(self.value & other.value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CallConfig):
            raise TealInputError("OCMethodConfig must be compared with same class")
        return self.value == other.value


CallConfig.__module__ = "pyteal"


@dataclass(frozen=True)
class CallConfigs:
    """
    CallConfigs keep track of one method registration's CallConfigs for all OnComplete cases.
    """

    no_op: CallConfig = field(kw_only=True, default=CallConfig.CALL)
    opt_in: CallConfig = field(kw_only=True, default=CallConfig.NEVER)
    close_out: CallConfig = field(kw_only=True, default=CallConfig.NEVER)
    clear_state: CallConfig = field(kw_only=True, default=CallConfig.NEVER)
    update_application: CallConfig = field(kw_only=True, default=CallConfig.NEVER)
    delete_application: CallConfig = field(kw_only=True, default=CallConfig.NEVER)

    def is_never(self) -> bool:
        return (
            self.no_op == CallConfig.NEVER
            and self.opt_in == CallConfig.NEVER
            and self.close_out == CallConfig.NEVER
            and self.clear_state == CallConfig.NEVER
            and self.update_application == CallConfig.NEVER
            and self.delete_application == CallConfig.NEVER
        )

    def _oc_under_call_config(self, call_config: CallConfig) -> list[EnumInt]:
        if not isinstance(call_config, CallConfig):
            raise TealInputError(
                "generate condition based on OCMethodCallConfigs should be based on OCMethodConfig"
            )
        config_oc_pairs: list[tuple[CallConfig, EnumInt]] = [
            (self.no_op, OnComplete.NoOp),
            (self.opt_in, OnComplete.OptIn),
            (self.close_out, OnComplete.CloseOut),
            (self.clear_state, OnComplete.ClearState),
            (self.update_application, OnComplete.UpdateApplication),
            (self.delete_application, OnComplete.DeleteApplication),
        ]
        return [
            oc
            for oc_config, oc in config_oc_pairs
            if (oc_config & call_config) != CallConfig.NEVER
        ]

    def _partition_oc_by_clear_state(
        self, cc: CallConfig
    ) -> tuple[bool, list[EnumInt]]:
        not_clear_states, clear_states = more_itertools.partition(
            lambda x: str(x) == str(OnComplete.ClearState),
            self._oc_under_call_config(cc),
        )
        return len(list(clear_states)) > 0, list(not_clear_states)


@dataclass(frozen=True)
class OCAction:
    """
    OnComplete Action, registers bare calls to one single OnCompletion case.
    """

    on_create: Optional[Expr | SubroutineFnWrapper | ABIReturnSubroutine] = field(
        kw_only=True, default=None
    )
    on_call: Optional[Expr | SubroutineFnWrapper | ABIReturnSubroutine] = field(
        kw_only=True, default=None
    )

    @staticmethod
    def never() -> "OCAction":
        return OCAction()

    @staticmethod
    def create_only(
        f: Expr | SubroutineFnWrapper | ABIReturnSubroutine,
    ) -> "OCAction":
        return OCAction(on_create=f)

    @staticmethod
    def call_only(
        f: Expr | SubroutineFnWrapper | ABIReturnSubroutine,
    ) -> "OCAction":
        return OCAction(on_call=f)

    @staticmethod
    def always(
        f: Expr | SubroutineFnWrapper | ABIReturnSubroutine,
    ) -> "OCAction":
        return OCAction(on_create=f, on_call=f)


OCAction.__module__ = "pyteal"


@dataclass(frozen=True)
class OCActions:
    """
    OnCompletion Actions keep track of bare-call registrations to all OnCompletion cases.
    """

    close_out: OCAction = field(kw_only=True, default=OCAction.never())
    clear_state: OCAction = field(kw_only=True, default=OCAction.never())
    delete_application: OCAction = field(kw_only=True, default=OCAction.never())
    no_op: OCAction = field(kw_only=True, default=OCAction.never())
    opt_in: OCAction = field(kw_only=True, default=OCAction.never())
    update_application: OCAction = field(kw_only=True, default=OCAction.never())

    def dictify(self) -> dict[EnumInt, OCAction]:
        return {
            OnComplete.CloseOut: self.close_out,
            OnComplete.ClearState: self.clear_state,
            OnComplete.DeleteApplication: self.delete_application,
            OnComplete.NoOp: self.no_op,
            OnComplete.OptIn: self.opt_in,
            OnComplete.UpdateApplication: self.update_application,
        }

    def is_empty(self) -> bool:
        for oc_action in self.dictify().values():
            if oc_action.on_call is not None or oc_action.on_create is not None:
                return False
        return True


OCActions.__module__ = "pyteal"


@dataclass(frozen=True)
class CondNode:
    condition: Expr
    branch: Expr


CondNode.__module__ = "pyteal"


@dataclass
class CategorizedCondNodes:
    method_calls_create: list[CondNode] = field(default_factory=list)
    bare_calls_create: list[CondNode] = field(default_factory=list)
    method_calls: list[CondNode] = field(default_factory=list)
    bare_calls: list[CondNode] = field(default_factory=list)

    def program_construction(self) -> Expr:
        concatenated_ast = (
            self.method_calls_create
            + self.bare_calls_create
            + self.method_calls
            + self.bare_calls
        )
        if len(concatenated_ast) == 0:
            raise TealInputError("ABIRouter: Cannot build program with an empty AST")
        program: Cond = Cond(*[[n.condition, n.branch] for n in concatenated_ast])
        return program


CategorizedCondNodes.__module__ = "pyteal"


class Router:
    """
    Class that help constructs:
    - an ARC-4 app's approval/clear-state programs
    - and a contract JSON object allowing for easily read and call methods in the contract
    """

    def __init__(
        self,
        name: str,
        bare_calls: OCActions,
    ) -> None:
        """
        Args:
            name: the name of the smart contract, used in the JSON object.
            bare_calls: the bare app call registered for each on_completion.
        """

        self.name: str = name
        self.categorized_approval_ast = CategorizedCondNodes()
        self.categorized_clear_state_ast = CategorizedCondNodes()
        self.added_method_sig: set[str] = set()

        self.__add_bare_call(bare_calls)

    @staticmethod
    def _wrap_handler(
        is_method_call: bool, handler: ABIReturnSubroutine | SubroutineFnWrapper | Expr
    ) -> Expr:
        """This is a helper function that handles transaction arguments passing in bare-app-call/abi-method handlers.

        If `is_abi_method` is True, then it can only be `ABIReturnSubroutine`,
        otherwise:
            - both `ABIReturnSubroutine` and `Subroutine` takes 0 argument on the stack.
            - all three cases have none (or void) type.

        On ABI method case, if the ABI method has more than 15 args, this function manages to de-tuple
        the last (16-th) Txn app-arg into a list of ABI method arguments, and pass in to the ABI method.

        Args:
            is_method_call: a boolean value that specify if the handler is an ABI method.
            handler: an `ABIReturnSubroutine`, or `SubroutineFnWrapper` (for `Subroutine` case), or an `Expr`.
        Returns:
            Expr:
                - for bare-appcall it returns an expression that the handler takes no txn arg and Approve
                - for abi-method it returns the txn args correctly decomposed into ABI variables,
                  passed in ABIReturnSubroutine and logged, then approve.
        """
        if not is_method_call:
            match handler:
                case Expr():
                    if handler.type_of() != TealType.none:
                        raise TealInputError(
                            f"bare appcall handler should be TealType.none not {handler.type_of()}."
                        )
                    return handler if handler.has_return() else Seq(handler, Approve())
                case SubroutineFnWrapper():
                    if handler.type_of() != TealType.none:
                        raise TealInputError(
                            f"subroutine call should be returning none not {handler.type_of()}."
                        )
                    if handler.subroutine.argument_count() != 0:
                        raise TealInputError(
                            f"subroutine call should take 0 arg for bare-app call. "
                            f"this subroutine takes {handler.subroutine.argument_count()}."
                        )
                    return Seq(handler(), Approve())
                case ABIReturnSubroutine():
                    if handler.type_of() != "void":
                        raise TealInputError(
                            f"abi-returning subroutine call should be returning void not {handler.type_of()}."
                        )
                    if handler.subroutine.argument_count() != 0:
                        raise TealInputError(
                            f"abi-returning subroutine call should take 0 arg for bare-app call. "
                            f"this abi-returning subroutine takes {handler.subroutine.argument_count()}."
                        )
                    return Seq(cast(Expr, handler()), Approve())
                case _:
                    raise TealInputError(
                        "bare appcall can only accept: none type Expr, or Subroutine/ABIReturnSubroutine with none return and no arg"
                    )
        else:
            if not isinstance(handler, ABIReturnSubroutine):
                raise TealInputError(
                    f"method call should be only registering ABIReturnSubroutine, got {type(handler)}."
                )
            if not handler.is_abi_routable():
                raise TealInputError(
                    f"method call ABIReturnSubroutine is not registrable"
                    f"got {handler.subroutine.argument_count()} args with {len(handler.subroutine.abi_args)} ABI args."
                )

            arg_type_specs = cast(
                list[abi.TypeSpec], handler.subroutine.expected_arg_types
            )
            if handler.subroutine.argument_count() > METHOD_ARG_NUM_LIMIT:
                last_arg_specs_grouped = arg_type_specs[METHOD_ARG_NUM_LIMIT - 1 :]
                arg_type_specs = arg_type_specs[: METHOD_ARG_NUM_LIMIT - 1]
                last_arg_spec = abi.TupleTypeSpec(*last_arg_specs_grouped)
                arg_type_specs.append(last_arg_spec)

            arg_abi_vars: list[abi.BaseType] = [
                type_spec.new_instance() for type_spec in arg_type_specs
            ]
            decode_instructions: list[Expr] = [
                arg_abi_vars[i].decode(Txn.application_args[i + 1])
                for i in range(len(arg_type_specs))
            ]

            if handler.subroutine.argument_count() > METHOD_ARG_NUM_LIMIT:
                tuple_arg_type_specs: list[abi.TypeSpec] = cast(
                    list[abi.TypeSpec],
                    handler.subroutine.expected_arg_types[METHOD_ARG_NUM_LIMIT - 1 :],
                )
                tuple_abi_args: list[abi.BaseType] = [
                    t_arg_ts.new_instance() for t_arg_ts in tuple_arg_type_specs
                ]
                last_tuple_arg: abi.Tuple = cast(abi.Tuple, arg_abi_vars[-1])
                de_tuple_instructions: list[Expr] = [
                    last_tuple_arg[i].store_into(tuple_abi_args[i])
                    for i in range(len(tuple_arg_type_specs))
                ]
                decode_instructions += de_tuple_instructions
                arg_abi_vars = arg_abi_vars[:-1] + tuple_abi_args

            # NOTE: does not have to have return, can be void method
            if handler.type_of() == "void":
                return Seq(
                    *decode_instructions,
                    cast(Expr, handler(*arg_abi_vars)),
                    Approve(),
                )
            else:
                output_temp: abi.BaseType = cast(
                    OutputKwArgInfo, handler.output_kwarg_info
                ).abi_type.new_instance()
                subroutine_call: abi.ReturnedValue = cast(
                    abi.ReturnedValue, handler(*arg_abi_vars)
                )
                return Seq(
                    *decode_instructions,
                    subroutine_call.store_into(output_temp),
                    abi.MethodReturn(output_temp),
                    Approve(),
                )

    def __add_bare_call(self, oc_actions: OCActions) -> None:
        if oc_actions.is_empty():
            raise TealInputError("the OnCompleteActions is empty.")
        bare_app_calls: dict[EnumInt, OCAction] = oc_actions.dictify()

        cs_calls = bare_app_calls[OnComplete.ClearState]
        if cs_calls.on_call is not None:
            on_call = cast(
                Expr | SubroutineFnWrapper | ABIReturnSubroutine,
                cs_calls.on_call,
            )
            wrapped = Router._wrap_handler(False, on_call)
            self.categorized_clear_state_ast.bare_calls.append(
                CondNode(Int(1), wrapped)
            )
        if cs_calls.on_create is not None:
            on_create = cast(
                Expr | SubroutineFnWrapper | ABIReturnSubroutine,
                cs_calls.on_create,
            )
            wrapped = Router._wrap_handler(False, on_create)
            self.categorized_clear_state_ast.bare_calls_create.append(
                CondNode(Txn.application_id() == Int(0), wrapped)
            )

        approval_calls = {
            oc: oc_action
            for oc, oc_action in bare_app_calls.items()
            if str(oc) != str(OnComplete.ClearState)
        }

        for oc, approval_bac in approval_calls.items():
            if approval_bac.on_call:
                on_call = cast(
                    Expr | SubroutineFnWrapper | ABIReturnSubroutine,
                    approval_bac.on_call,
                )
                wrapped = Router._wrap_handler(False, on_call)
                self.categorized_approval_ast.bare_calls.append(
                    CondNode(Txn.on_completion() == oc, wrapped)
                )
            if approval_bac.on_create:
                on_create = cast(
                    Expr | SubroutineFnWrapper | ABIReturnSubroutine,
                    approval_bac.on_create,
                )
                wrapped = Router._wrap_handler(False, on_create)
                self.categorized_approval_ast.bare_calls_create.append(
                    CondNode(
                        And(Txn.application_id() == Int(0), Txn.on_completion() == oc),
                        wrapped,
                    )
                )

    def add_method_handler(
        self,
        method_call: ABIReturnSubroutine,
        method_overload_name: str = None,
        call_configs: CallConfigs = CallConfigs(),
    ) -> None:
        if not isinstance(method_call, ABIReturnSubroutine):
            raise TealInputError(
                "for adding method handler, must be ABIReturnSubroutine"
            )
        method_signature = method_call.method_signature(method_overload_name)
        if call_configs.is_never():
            raise TealInputError(
                f"registered method {method_signature} is never executed"
            )
        if method_signature in self.added_method_sig:
            raise TealInputError(f"re-registering method {method_signature} detected")
        self.added_method_sig.add(method_signature)

        wrapped = Router._wrap_handler(True, method_call)

        (
            create_has_clear_state,
            create_others,
        ) = call_configs._partition_oc_by_clear_state(CallConfig.CREATE)
        if create_has_clear_state:
            self.categorized_clear_state_ast.method_calls_create.append(
                CondNode(
                    And(
                        Txn.application_id() == Int(0),
                        Txn.application_args[0] == MethodSignature(method_signature),
                    ),
                    wrapped,
                )
            )

        call_has_clear_state, call_others = call_configs._partition_oc_by_clear_state(
            CallConfig.CALL
        )
        if call_has_clear_state:
            self.categorized_clear_state_ast.method_calls.append(
                CondNode(
                    Txn.application_args[0] == MethodSignature(method_signature),
                    wrapped,
                )
            )

        if create_others:
            self.categorized_approval_ast.method_calls_create.append(
                CondNode(
                    And(
                        Txn.application_id() == Int(0),
                        Txn.application_args[0] == MethodSignature(method_signature),
                        Or(*[Txn.on_completion() == oc for oc in create_others]),
                    ),
                    wrapped,
                )
            )
        if call_others:
            self.categorized_approval_ast.method_calls.append(
                CondNode(
                    And(
                        Txn.application_args[0] == MethodSignature(method_signature),
                        Or(*[Txn.on_completion() == oc for oc in call_others]),
                    ),
                    wrapped,
                )
            )

    def contract_construct(self) -> dict[str, Any]:
        """A helper function in constructing contract JSON object.

        It takes out the method signatures from approval program `ProgramNode`'s,
        and constructs an `Contract` object.

        Returns:
            contract: a dictified `Contract` object constructed from
                approval program's method signatures and `self.name`.
        """
        method_collections = [
            sdk_abi.Method.from_signature(sig) for sig in self.added_method_sig
        ]
        return sdk_abi.Contract(self.name, method_collections).dictify()

    def build_program(self) -> tuple[Expr, Expr, dict[str, Any]]:
        """
        Constructs ASTs for approval and clear-state programs from the registered methods in the router,
        also generates a JSON object of contract to allow client read and call the methods easily.

        Returns:
            approval_program: AST for approval program
            clear_state_program: AST for clear-state program
            contract: JSON object of contract to allow client start off-chain call
        """
        return (
            self.categorized_approval_ast.program_construction(),
            self.categorized_clear_state_ast.program_construction(),
            self.contract_construct(),
        )

    def compile_program(
        self,
        *,
        version: int = DEFAULT_TEAL_VERSION,
        assembleConstants: bool = False,
        optimize: OptimizeOptions = None,
    ) -> tuple[str, str, dict[str, Any]]:
        """
        Combining `build_program` and `compileTeal`, compiles built Approval and ClearState programs
        and returns Contract JSON object for off-chain calling.

        Returns:
            approval_program: compiled approval program
            clear_state_program: compiled clear-state program
            contract: JSON object of contract to allow client start off-chain call
        """
        ap, csp, contract = self.build_program()
        ap_compiled = compileTeal(
            ap,
            Mode.Application,
            version=version,
            assembleConstants=assembleConstants,
            optimize=optimize,
        )
        csp_compiled = compileTeal(
            csp,
            Mode.Application,
            version=version,
            assembleConstants=assembleConstants,
            optimize=optimize,
        )
        return ap_compiled, csp_compiled, contract


Router.__module__ = "pyteal"
