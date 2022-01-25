from typing import List, Union
from algosdk.future.transaction import OnComplete
from pyteal.ast import *

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
    return_event_selector = Bytes("base16", "151f7c75")

    def __init__(self) -> None:
        pass

    def onBareAppCall(
        self,
        bareAppCall: Subroutine,
        onCompletes: Union[OnComplete, List[OnComplete]],
        creation: bool,
    ) -> None:
        condList = [Txn.application_args.length() == Int(0)]
        if creation:
            condList.append(Txn.application_id() == Int(0))

        if isinstance(onCompletes, list):
            for i in onCompletes:
                condList.append(Txn.on_completion() == i)
        else:
            condList.append(Txn.on_completion() == onCompletes)

        triggerCond = And(*condList)


    def bareAppCall(self) -> None:
        # Decorator form of onBareAppCall
        pass

    def onMethodCall(
        self,
        methodAppCall: Subroutine,
        onComplete: OnComplete,
        creation: bool,
    ) -> None:
        # trigger condition: txna ApplicationArgs 0 == MethodSignature(methodAppCall.name) and onComplete == self.onComplete
        # if create app id == 0
        # TODO unpack the arguments and pass them to handler function
        # MethodSignature(methodAppCall.name)
        # TODO take return value from handler and prefix + log
        # Log(Concat(return_event_selector, ...))
        pass

    def methodCall(self) -> None:
        # Decorator form of methodCall
        pass

    def buildProgram(self) -> None:
        pass
