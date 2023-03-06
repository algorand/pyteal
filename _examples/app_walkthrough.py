import json
from pyteal import (
    App,
    Approve,
    Assert,
    BareCallActions,
    Bytes,
    Cond,
    Global,
    If,
    Int,
    Mode,
    OnComplete,
    OnCompleteAction,
    Reject,
    Return,
    Router,
    ScratchVar,
    Seq,
    TealType,
    Txn,
    compileTeal,
)


def step_1():
    # example: APP_EMPTY_LOGIC
    def approval_program():
        program = Return(Int(1))
        # Mode.Application specifies that this is a smart contract
        return compileTeal(program, Mode.Application, version=5)

    def clear_state_program():
        program = Return(Int(1))
        # Mode.Application specifies that this is a smart contract
        return compileTeal(program, Mode.Application, version=5)

    print(approval_program())
    print(clear_state_program())
    # example: APP_EMPTY_LOGIC


def app_manual_router():
    # example: APP_MANUAL_ROUTER
    def approval_program():

        handle_creation = Approve()
        handle_optin = Reject()
        handle_closeout = Reject()
        handle_update = Reject()
        handle_delete = Reject()
        handle_noop = Reject()

        program = Cond(
            [Txn.application_id() == Int(0), handle_creation],
            [Txn.on_completion() == OnComplete.OptIn, handle_optin],
            [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
            [Txn.on_completion() == OnComplete.UpdateApplication, handle_update],
            [Txn.on_completion() == OnComplete.DeleteApplication, handle_delete],
            [Txn.on_completion() == OnComplete.NoOp, handle_noop],
        )
        return program

    return compileTeal(approval_program(), Mode.Application, version=5)
    # example: APP_MANUAL_ROUTER
