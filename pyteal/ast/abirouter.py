from typing import List, NamedTuple, Tuple, Union, cast

from ..config import RETURN_EVENT_SELECTOR
from ..errors import TealInputError
from ..types import TealType

from .app import OnComplete
from .expr import Expr
from .int import EnumInt, Int
from .if_ import If
from .methodsig import MethodSignature
from .unaryexpr import Log
from .naryexpr import And, Concat, Or
from .return_ import Approve, Reject
from .seq import Seq
from .subroutine import SubroutineFnWrapper
from .txn import Txn


"""
Notes:
- On a BareApp Call, check
  - [x] txn NumAppArgs == 0
  - [x] On-Completion should match (can be a list of On-Completion here)
  - [x] Must execute actions required to invoke the method

- On Method Call, check
  - [x] txna ApplicationArgs 0 == method "method-signature"
  - [x] On-Completion should match (only one On-Completion specified here?)
  - [?] non void method call should log with 0x151f7c75 return-method-specifier (kinda done in another PR to ABI-Type)
  - [?] redirect the method arguments and pass them to handler function (kinda done, but need to do with extraction and (en/de)-code)
  - [ ] Must execute actions required to invoke the method
  - [ ] extract arguments if needed (decode txna ApplicationArgs 15 if there exists, and extract arguments to feed method)

Notes for OC:
- creation conflict with closeout and clearstate
- must check: txn ApplicationId == 0 for creation
- clearstate AST build should be separated with other OC AST build
"""


class ProgramNode(NamedTuple):
    condition: Expr
    branch: Expr


class ABIRouter:
    def __init__(self) -> None:
        self.approvalIfThen: List[ProgramNode] = []
        self.clearStateIfThen: List[ProgramNode] = []

    @staticmethod
    def parseConditions(
        mReg: Union[SubroutineFnWrapper, None],
        onCompletes: List[EnumInt],
        creation: bool,
    ) -> Tuple[List[Expr], List[Expr]]:
        # Check if it is a *CREATION*
        approvalConds: List[Expr] = [Txn.application_id() == Int(0)] if creation else []
        clearStateConds: List[Expr] = []

        # Check if current condition is for *ABI METHOD* (method selector && numAppArg == 1 + subroutineSyntaxArgNum)
        #       or *BARE APP CALL* (numAppArg == 0)
        methodOrBareCondition = (
            And(
                Txn.application_args.length()
                == Int(1 + len(mReg.subroutine.implementationParams)),
                Txn.application_args[0] == MethodSignature(mReg.name()),
            )
            if mReg is not None
            else Txn.application_args.length() == Int(0)
        )
        approvalConds.append(methodOrBareCondition)

        # Check the existence of OC.CloseOut
        closeOutExist = any(map(lambda x: x == OnComplete.CloseOut, onCompletes))
        # Check the existence of OC.ClearState (needed later)
        clearStateExist = any(map(lambda x: x == OnComplete.ClearState, onCompletes))
        # Ill formed report if app create with existence of OC.CloseOut or OC.ClearState
        if creation and (closeOutExist or clearStateExist):
            raise TealInputError(
                "OnComplete ClearState/CloseOut may be ill-formed with app creation"
            )
        # if OC.ClearState exists, add method-or-bare-condition since it is only needed in ClearStateProgram
        if clearStateExist:
            clearStateConds.append(methodOrBareCondition)

        # Check onComplete conditions for approvalConds, filter out *ClearState*
        approvalOcConds: List[Expr] = [
            Txn.on_completion() == oc
            for oc in onCompletes
            if oc != OnComplete.ClearState
        ]

        # if approval OC condition is not empty, append Or to approvalConds
        if len(approvalOcConds) > 0:
            approvalConds.append(Or(*approvalOcConds))

        # what we have here is:
        # list of conds for approval program on one branch: creation?, method/bare, Or[OCs]
        # list of conds for clearState program on one branch: method/bare
        return approvalConds, clearStateConds

    @staticmethod
    def wrapHandler(isMethod: bool, branch: Union[SubroutineFnWrapper, Expr]) -> Expr:
        exprList: List[Expr] = []
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
                    "For bare app call: should only register Seq (with no ret) or Subroutine (with ret but none type)"
                )
        else:
            if isinstance(branch, SubroutineFnWrapper) and branch.has_return():
                # TODO need to encode/decode things

                execBranch: Expr = branch(
                    *[
                        Txn.application_args[i + 1]
                        for i in range(len(branch.subroutine.implementationParams))
                    ]
                )

                exprList.append(
                    Log(Concat(RETURN_EVENT_SELECTOR, execBranch))
                    if branch.type_of() != TealType.none
                    else execBranch
                )
            else:
                raise TealInputError(
                    "For method call: should only register Subroutine with return"
                )
        exprList.append(Approve())
        return Seq(*exprList)

    def __appendToAST(
        self, approvalConds: List[Expr], clearConds: List[Expr], branch: Expr
    ) -> None:
        if len(approvalConds) > 0:
            self.approvalIfThen.append(
                ProgramNode(
                    And(*approvalConds) if len(approvalConds) > 1 else approvalConds[0],
                    branch,
                )
            )
        if len(clearConds) > 0:
            self.clearStateIfThen.append(
                ProgramNode(
                    And(*clearConds) if len(clearConds) > 1 else clearConds[0],
                    branch,
                )
            )

    def onBareAppCall(
        self,
        bareAppCall: Union[SubroutineFnWrapper, Expr],
        onCompletes: Union[EnumInt, List[EnumInt]],
        creation: bool = False,
    ) -> None:
        ocList: List[EnumInt] = (
            cast(List[EnumInt], onCompletes)
            if isinstance(onCompletes, list)
            else [cast(EnumInt, onCompletes)]
        )
        approvalConds, clearConds = ABIRouter.parseConditions(
            mReg=None, onCompletes=ocList, creation=creation
        )
        branch = ABIRouter.wrapHandler(False, bareAppCall)
        self.__appendToAST(approvalConds, clearConds, branch)

    def onMethodCall(
        self,
        methodAppCall: SubroutineFnWrapper,
        onComplete: EnumInt = OnComplete.NoOp,
        creation: bool = False,
    ) -> None:
        ocList: List[EnumInt] = [cast(EnumInt, onComplete)]
        approvalConds, clearConds = ABIRouter.parseConditions(
            mReg=methodAppCall, onCompletes=ocList, creation=creation
        )
        branch = ABIRouter.wrapHandler(True, methodAppCall)
        self.__appendToAST(approvalConds, clearConds, branch)

    @staticmethod
    def astConstruct(astList: List[ProgramNode]) -> Expr:
        program: If = If(astList[0].condition).Then(astList[0].branch)
        for i in range(1, len(astList)):
            program.ElseIf(astList[i].condition).Then(astList[i].branch)
        program.Else(Reject())
        return program

    def buildProgram(self) -> Tuple[Expr, Expr]:
        # TODO need to recheck how the program is built
        # question: if there's no approval condition/branch registered, shall it reject/approve everything?
        # similarly, if there's no clearstate condition/branch registered, shall it reject/approve everything?
        return (
            ABIRouter.astConstruct(self.approvalIfThen),
            ABIRouter.astConstruct(self.clearStateIfThen),
        )


ABIRouter.__module__ = "pyteal"
