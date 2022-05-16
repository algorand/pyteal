from algosdk.abi import Contract, Method
from dataclasses import dataclass
from typing import Any, cast, Optional

from pyteal.config import METHOD_ARG_NUM_LIMIT
from pyteal.errors import TealInputError
from pyteal.types import TealType

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

"""
Notes:
- On a BareApp Call, check
  - [x] txn NumAppArgs == 0
  - [x] On-Completion should match (can be a list of On-Completion here)
  - [x] Must execute actions required to invoke the method

- On Method Call, check
  - [x] txna ApplicationArgs 0 == method "method-signature"
  - [x] On-Completion should match (only one On-Completion specified here?)
  - [x] non void method call should log with 0x151f7c75 return-method-specifier
        (kinda done in another PR to ABI-Type)
  - [x] redirect the method arguments and pass them to handler function
        (kinda done, but need to do with extraction and (en/de)-code)
  - [x] Must execute actions required to invoke the method
  - [x] extract arguments if needed
        (decode txna ApplicationArgs 15 if there exists, and extract arguments to feed method)

Notes for OC:
- creation conflict with closeout and clearstate
- must check: txn ApplicationId == 0 for creation
- clearstate AST build should be separated with other OC AST build
"""


@dataclass
class ProgramNode:
    condition: Expr
    branch: Expr
    method_info: Optional[Method]


ProgramNode.__module__ = "pyteal"


class Router:
    """ """

    def __init__(self, name: Optional[str] = None) -> None:
        self.name: str = "Contract" if name is None else name
        self.approval_if_then: list[ProgramNode] = []
        self.clear_state_if_then: list[ProgramNode] = []

    @staticmethod
    def __parse_conditions(
        method_signature: str,
        method_to_register: ABIReturnSubroutine | None,
        on_completes: list[EnumInt],
        creation: bool,
    ) -> tuple[list[Expr], list[Expr]]:
        """ """
        # Check if it is a *CREATION*
        approval_conds: list[Expr] = (
            [Txn.application_id() == Int(0)] if creation else []
        )
        clear_state_conds: list[Expr] = []

        if method_signature == "" and method_to_register is not None:
            raise TealInputError(
                "A method_signature must only be provided if method_to_register is not None"
            )

        # Check:
        # - if current condition is for *ABI METHOD*
        #   (method selector && numAppArg == 1 + min(METHOD_APP_ARG_NUM_LIMIT, subroutineSyntaxArgNum))
        # - or *BARE APP CALL* (numAppArg == 0)
        method_or_bare_condition = (
            And(
                Txn.application_args[0] == MethodSignature(method_signature),
                Txn.application_args.length()
                == Int(
                    1
                    + min(
                        method_to_register.subroutine.argument_count(),
                        METHOD_ARG_NUM_LIMIT,
                    )
                ),
            )
            if method_to_register is not None
            else Txn.application_args.length() == Int(0)
        )
        approval_conds.append(method_or_bare_condition)

        # Check the existence of OC.CloseOut
        close_out_exist = any(
            map(lambda x: str(x) == str(OnComplete.CloseOut), on_completes)
        )
        # Check the existence of OC.ClearState (needed later)
        clear_state_exist = any(
            map(lambda x: str(x) == str(OnComplete.ClearState), on_completes)
        )
        # Ill formed report if app create with existence of OC.CloseOut or OC.ClearState
        if creation and (close_out_exist or clear_state_exist):
            raise TealInputError(
                "OnComplete ClearState/CloseOut may be ill-formed with app creation"
            )
        # if OC.ClearState exists, add method-or-bare-condition since it is only needed in ClearStateProgram
        if clear_state_exist:
            clear_state_conds.append(method_or_bare_condition)

        # Check onComplete conditions for approval_conds, filter out *ClearState*
        approval_oc_conds: list[Expr] = [
            Txn.on_completion() == oc
            for oc in on_completes
            if str(oc) != str(OnComplete.ClearState)
        ]

        # if approval OC condition is not empty, append Or to approval_conds
        if len(approval_oc_conds) > 0:
            approval_conds.append(Or(*approval_oc_conds))

        # what we have here is:
        # list of conds for approval program on one branch: creation?, method/bare, Or[OCs]
        # list of conds for clearState program on one branch: method/bare
        return approval_conds, clear_state_conds

    @staticmethod
    def __wrap_handler(
        is_abi_method: bool, handler: ABIReturnSubroutine | SubroutineFnWrapper | Expr
    ) -> Expr:
        """"""
        if not is_abi_method:
            match handler:
                case Expr():
                    if handler.type_of() != TealType.none:
                        raise TealInputError(
                            "bare appcall handler should have type to be none."
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
                        "bare appcall can only accept: none type + Seq (no ret) or Subroutine (with ret)"
                    )
        else:
            if not isinstance(handler, ABIReturnSubroutine):
                raise TealInputError(
                    f"method call should be only registering ABIReturnSubroutine, got {type(handler)}."
                )
            if not handler.is_registrable():
                raise TealInputError(
                    f"method call ABIReturnSubroutine is not registable"
                    f"got {handler.subroutine.argument_count()} args with {len(handler.subroutine.abi_args)} ABI args."
                )

            arg_type_specs: list[abi.TypeSpec] = cast(
                list[abi.TypeSpec], handler.subroutine.expected_arg_types
            )
            if handler.subroutine.argument_count() > METHOD_ARG_NUM_LIMIT:
                to_be_tupled_specs = arg_type_specs[METHOD_ARG_NUM_LIMIT - 1 :]
                arg_type_specs = arg_type_specs[: METHOD_ARG_NUM_LIMIT - 1]
                tupled_spec = abi.TupleTypeSpec(*to_be_tupled_specs)
                arg_type_specs.append(tupled_spec)

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
                tupled_arg: abi.Tuple = cast(abi.Tuple, arg_abi_vars[-1])
                de_tuple_instructions: list[Expr] = [
                    tupled_arg[i].store_into(tuple_abi_args[i])
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

    def __append_to_ast(
        self,
        approval_conditions: list[Expr],
        clear_state_conditions: list[Expr],
        branch: Expr,
        method_obj: Optional[Method] = None,
    ) -> None:
        """ """
        if len(approval_conditions) > 0:
            self.approval_if_then.append(
                ProgramNode(
                    And(*approval_conditions)
                    if len(approval_conditions) > 1
                    else approval_conditions[0],
                    branch,
                    method_obj,
                )
            )
        if len(clear_state_conditions) > 0:
            self.clear_state_if_then.append(
                ProgramNode(
                    And(*clear_state_conditions)
                    if len(clear_state_conditions) > 1
                    else clear_state_conditions[0],
                    branch,
                    method_obj,
                )
            )

    def add_bare_call(
        self,
        bare_app_call: ABIReturnSubroutine | SubroutineFnWrapper | Expr,
        on_completes: EnumInt | list[EnumInt],
        *,
        creation: bool = False,
    ) -> None:
        """ """
        ocList: list[EnumInt] = (
            cast(list[EnumInt], on_completes)
            if isinstance(on_completes, list)
            else [cast(EnumInt, on_completes)]
        )
        approval_conds, clear_state_conds = Router.__parse_conditions(
            method_signature="",
            method_to_register=None,
            on_completes=ocList,
            creation=creation,
        )
        branch = Router.__wrap_handler(False, bare_app_call)
        self.__append_to_ast(approval_conds, clear_state_conds, branch, None)

    def add_method_handler(
        self,
        method_app_call: ABIReturnSubroutine,
        *,
        method_signature: str = None,
        on_complete: EnumInt = OnComplete.NoOp,
        creation: bool = False,
    ) -> None:
        """ """
        oc_list: list[EnumInt] = [cast(EnumInt, on_complete)]

        if method_signature is None:
            method_signature = method_app_call.method_signature()

        approval_conds, clear_state_conds = Router.__parse_conditions(
            method_signature=method_signature,
            method_to_register=method_app_call,
            on_completes=oc_list,
            creation=creation,
        )
        branch = Router.__wrap_handler(True, method_app_call)
        self.__append_to_ast(
            approval_conds,
            clear_state_conds,
            branch,
            Method.from_signature(method_signature),
        )

    @staticmethod
    def __ast_construct(
        ast_list: list[ProgramNode],
    ) -> Expr:
        """ """
        if len(ast_list) == 0:
            raise TealInputError("ABIRouter: Cannot build program with an empty AST")

        program: Cond = Cond(*[[node.condition, node.branch] for node in ast_list])

        return program

    def __contract_construct(self) -> dict[str, Any]:
        method_collections = [
            node.method_info for node in self.approval_if_then if node.method_info
        ]
        return Contract(self.name, method_collections).dictify()

    def build_program(self) -> tuple[Expr, Expr, dict[str, Any]]:
        """This method construct ASTs for both the approval and clear programs based on the inputs to the router,
        also dump a JSON object of contract to allow client read and call the methods easily.

        """
        return (
            Router.__ast_construct(self.approval_if_then),
            Router.__ast_construct(self.clear_state_if_then)
            if self.clear_state_if_then
            else Approve(),
            self.__contract_construct(),
        )


Router.__module__ = "pyteal"
