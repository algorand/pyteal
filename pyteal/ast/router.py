from typing import cast
from dataclasses import dataclass

from pyteal.config import METHOD_ARG_NUM_LIMIT
from pyteal.errors import TealInputError
from pyteal.types import TealType
from pyteal.ast.subroutine import SubroutineFnWrapper

# from pyteal.ast import abi
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
  - [?] non void method call should log with 0x151f7c75 return-method-specifier
        (kinda done in another PR to ABI-Type)
  - [?] redirect the method arguments and pass them to handler function
        (kinda done, but need to do with extraction and (en/de)-code)
  - [ ] Must execute actions required to invoke the method
  - [ ] extract arguments if needed
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


ProgramNode.__module__ = "pyteal"


class Router:
    """ """

    def __init__(self) -> None:
        self.approval_if_then: list[ProgramNode] = []
        self.clear_state_if_then: list[ProgramNode] = []

    @staticmethod
    def __parse_conditions(
        method_to_register: SubroutineFnWrapper | None,
        on_completes: list[EnumInt],
        creation: bool,
    ) -> tuple[list[Expr], list[Expr]]:
        """ """
        # Check if it is a *CREATION*
        approval_conds: list[Expr] = (
            [Txn.application_id() == Int(0)] if creation else []
        )
        clear_state_conds: list[Expr] = []

        # Check:
        # - if current condition is for *ABI METHOD*
        #   (method selector && numAppArg == max(METHOD_APP_ARG_NUM_LIMIT, 1 + subroutineSyntaxArgNum))
        # - or *BARE APP CALL* (numAppArg == 0)
        method_or_bare_condition = (
            And(
                Txn.application_args[0] == MethodSignature(method_to_register.name()),
                Txn.application_args.length()
                == Int(
                    1
                    + max(
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
        close_out_exist = any(map(lambda x: x == OnComplete.CloseOut, on_completes))
        # Check the existence of OC.ClearState (needed later)
        clear_state_exist = any(map(lambda x: x == OnComplete.ClearState, on_completes))
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
            if oc != OnComplete.ClearState
        ]

        # if approval OC condition is not empty, append Or to approval_conds
        if len(approval_oc_conds) > 0:
            approval_conds.append(Or(*approval_oc_conds))

        # what we have here is:
        # list of conds for approval program on one branch: creation?, method/bare, Or[OCs]
        # list of conds for clearState program on one branch: method/bare
        return approval_conds, clear_state_conds

    @staticmethod
    def __wrap_handler(isMethod: bool, branch: SubroutineFnWrapper | Expr) -> Expr:
        """"""
        exprList: list[Expr] = []
        if not isMethod:
            if (
                isinstance(branch, Seq)
                and not branch.has_return()
                and branch.type_of() == TealType.none
            ):
                exprList.append(branch)
            elif (
                isinstance(branch, SubroutineFnWrapper)
                and branch.has_return()
                and branch.type_of() == TealType.none
            ):
                exprList.append(branch())
            else:
                raise TealInputError(
                    "bare appcall can only accept: none type + Seq (no ret) or Subroutine (with ret)"
                )
        else:
            if isinstance(branch, SubroutineFnWrapper) and branch.has_return():
                # TODO need to encode/decode things
                # execBranchArgs: List[Expr] = []
                if branch.subroutine.argument_count() >= METHOD_ARG_NUM_LIMIT:
                    # NOTE decode (if arg num > 15 need to de-tuple 15th (last) argument)
                    pass
                else:
                    pass

                # exprList.append(
                # TODO this line can be changed to method-return in ABI side
                # MethodReturn(branch(*execBranchArgs))
                # if branch.type_of() != TealType.none
                # else branch(*execBranchArgs)
                # )
            else:
                raise TealInputError(
                    "For method call: should only register Subroutine with return"
                )
        exprList.append(Approve())
        return Seq(*exprList)

    def __append_to_ast(
        self, approval_conds: list[Expr], clear_state_conds: list[Expr], branch: Expr
    ) -> None:
        """ """
        if len(approval_conds) > 0:
            self.approval_if_then.append(
                ProgramNode(
                    And(*approval_conds)
                    if len(approval_conds) > 1
                    else approval_conds[0],
                    branch,
                )
            )
        if len(clear_state_conds) > 0:
            self.clear_state_if_then.append(
                ProgramNode(
                    And(*clear_state_conds)
                    if len(clear_state_conds) > 1
                    else clear_state_conds[0],
                    branch,
                )
            )

    def on_bare_app_call(
        self,
        bare_app_call: SubroutineFnWrapper | Expr,
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
            method_to_register=None, on_completes=ocList, creation=creation
        )
        branch = Router.__wrap_handler(False, bare_app_call)
        self.__append_to_ast(approval_conds, clear_state_conds, branch)

    def on_method_call(
        self,
        method_signature: str,
        method_app_call: SubroutineFnWrapper,
        *,
        on_complete: EnumInt = OnComplete.NoOp,
        creation: bool = False,
    ) -> None:
        """ """
        oc_list: list[EnumInt] = [cast(EnumInt, on_complete)]
        approval_conds, clear_state_conds = Router.__parse_conditions(
            method_to_register=method_app_call, on_completes=oc_list, creation=creation
        )
        branch = Router.__wrap_handler(True, method_app_call)
        self.__append_to_ast(approval_conds, clear_state_conds, branch)

    @staticmethod
    def __ast_construct(
        ast_list: list[ProgramNode],
    ) -> Expr:
        """ """
        if len(ast_list) == 0:
            raise TealInputError("ABIRouter: Cannot build program with an empty AST")

        program: Cond = Cond(*[[node.condition, node.branch] for node in ast_list])

        return program

    def build_program(self) -> tuple[Expr, Expr]:
        # TODO need JSON object
        """ """
        return (
            Router.__ast_construct(self.approval_if_then),
            Router.__ast_construct(self.clear_state_if_then),
        )


Router.__module__ = "pyteal"
