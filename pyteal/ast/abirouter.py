from typing import Callable, List, Tuple, Union, cast

from pyteal.errors import TealInputError
from pyteal.config import RETURN_EVENT_SELECTOR

from .app import OnComplete
from .bytes import Bytes
from .expr import Expr
from .int import EnumInt, Int
from .if_ import If
from .methodsig import MethodSignature
from .naryexpr import And, Or
from .return_ import Approve, Reject
from .seq import Seq
from .subroutine import Subroutine, SubroutineDefinition
from .txn import Txn

"""
Implementing a Method
An ARC-4 app implementing a method:

MUST check if txn NumAppArgs equals 0. If true, then this is a bare application call. If the Contract supports bare application calls for the current transaction parameters (it SHOULD check the OnCompletion action and whether the transaction is creating the application), it MUST handle the call appropriately and either approve or reject the transaction. The following steps MUST be ignored in this case. Otherwise, if the Contract does not support this bare application call, the Contract MUST reject the transaction.

MUST examine txna ApplicationArgs 0 to identify the selector of the method being invoked. If the contract does not implement a method with that selector, the Contract MUST reject the transaction.

MUST execute the actions required to implement the method being invoked. In general, this works by branching to the body of the method indicated by the selector.

The code for that method MAY extract the arguments it needs, if any, from the application call arguments as described in the Encoding section. If the method has more than 15 arguments and the contract needs to extract an argument beyond the 14th, it MUST decode txna ApplicationArgs 15 as a tuple to access the arguments contained in it.

If the method is non-void, the application MUST encode the return value as described in the Encoding section and then log it with the prefix 151f7c75. Other values MAY be logged before the return value, but other values MUST NOT be logged after the return value.
"""


"""
onBareAppCall can be used to register a bare app call (defined in the ABI as a call with no arguments or return value). The allowed on completion actions must be specified, as well as whether the bare call can be invoked during creation or not.

onMethodCall can be used to register a method call. By default OnComplete.NoOp will be the only allowed on completion action, but others may be specified. Additionally, you can pass in a value for creation if this method call should be invoked during app creation or not.

Ideally the router would also unpack the arguments and pass them to the handler function, as well as take any return value from the handler function and prefix and log it appropriately. Though this might require some more thought to implement properly.

buildPrograms would construct ASTs for both the approval and clear programs based on the inputs to the router. If any routes can be accessed with OnComplete.ClearState, these routes will be added to the clear state program.
"""


class ABIRouter:
    def __init__(self) -> None:
        self.approvalIfThen: List[Tuple[Expr, Expr]] = []
        self.clearStateIfThen: List[Tuple[Expr, Expr]] = []

    @staticmethod
    def parseConditions(
        methodName: Union[str, None], onCompletes: List[EnumInt], creation: bool
    ) -> Tuple[List[Expr], List[Expr]]:
        # Check if it is a *CREATION*
        approvalConds: List[Expr] = [Txn.application_id() == Int(0)] if creation else []
        clearStateConds: List[Expr] = []

        # Check if current condition is for *ABI METHOD* (method selector) or *BARE APP CALL* (numAppArg == 0)
        methodOrBareCondition = (
            Txn.application_args[0] == MethodSignature(cast(str, methodName))
            if methodName is not None
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
    def wrapHandler(isMethod: bool, branch: Union[Callable[..., Expr], Expr]) -> Expr:
        # TODO
        return Seq([Approve()])

    def onBareAppCall(
        self,
        bareAppCall: Union[Callable[..., Expr], Expr],
        onCompletes: Union[EnumInt, List[EnumInt]],
        creation: bool = False,
    ) -> None:
        ocList: List[EnumInt] = (
            cast(List[EnumInt], onCompletes)
            if isinstance(onCompletes, list)
            else [cast(EnumInt, onCompletes)]
        )
        approvalConds, clearStateConds = ABIRouter.parseConditions(
            methodName=None, onCompletes=ocList, creation=creation
        )
        # execBareAppCall: Expr = bareAppCall() if isinstance(bareAppCall, Subroutine) else cast(Expr, bareAppCall)
        # TODO update then branch (either activate subroutine or run seq of expr), then approve
        thenBranch = ABIRouter.wrapHandler(False, bareAppCall)
        # self.approvalIfThen.append((triggerCond, thenBranch))

    def onMethodCall(
        self,
        methodSig: str,
        methodAppCall: Callable[..., Expr],
        onComplete: EnumInt = OnComplete.NoOp,
        creation: bool = False,
    ) -> None:
        ocList: List[EnumInt] = [cast(EnumInt, onComplete)]
        approvalConds, clearStateConds = ABIRouter.parseConditions(
            methodName=methodSig, onCompletes=ocList, creation=creation
        )
        # TODO unpack the arguments and pass them to handler function
        # TODO take return value from handler and prefix + log: Log(Concat(return_event_selector, ...))
        # TODO update then branch (either activate subroutine or run seq of expr), then approve
        thenBranch = ABIRouter.wrapHandler(True, methodAppCall)
        # self.approvalIfThen.append((triggerCond, thenBranch))

    def buildProgram(self) -> Expr:
        approvalProgram: If = If(self.approvalIfThen[0][0]).Then(
            self.approvalIfThen[0][1]
        )
        for i in range(1, len(self.approvalIfThen)):
            approvalProgram.ElseIf(self.approvalIfThen[i][0]).Then(
                self.approvalIfThen[i][1]
            )
        approvalProgram.Else(Reject())

        # TODO clear program
        return approvalProgram


ABIRouter.__module__ = "pyteal"
