from pyteal import (
    App,
    Bytes,
    Cond,
    Err,
    Global,
    Int,
    Mode,
    OnComplete,
    Return,
    Seq,
    Txn,
    compileTeal,
)


def opted_in():
    # example: APPL_CHECK_OPTEDIN
    program = App.optedIn(Int(0), Txn.application_id())
    print(compileTeal(program, Mode.Application))
    # example: APPL_CHECK_OPTEDIN


def global_ts():
    # example: GLOBAL_LATEST_TIMESTAMP
    program = Global.latest_timestamp() >= App.globalGet(Bytes("StartDate"))
    print(compileTeal(program, Mode.Application))
    # example: GLOBAL_LATEST_TIMESTAMP


def boilerplate():
    # example: BOILERPLATE
    # Handle each possible OnCompletion type. We don't have to worry about
    # handling ClearState, because the ClearStateProgram will execute in that
    # case, not the ApprovalProgram.
    def approval_program():
        handle_noop = Seq([Return(Int(1))])

        handle_optin = Seq([Return(Int(1))])

        handle_closeout = Seq([Return(Int(1))])

        handle_updateapp = Err()

        handle_deleteapp = Err()

        program = Cond(
            [Txn.on_completion() == OnComplete.NoOp, handle_noop],
            [Txn.on_completion() == OnComplete.OptIn, handle_optin],
            [Txn.on_completion() == OnComplete.CloseOut, handle_closeout],
            [Txn.on_completion() == OnComplete.UpdateApplication, handle_updateapp],
            [Txn.on_completion() == OnComplete.DeleteApplication, handle_deleteapp],
        )
        return program

    with open("boilerplate_approval_pyteal.teal", "w") as f:
        compiled = compileTeal(approval_program(), Mode.Application, version=5)
        f.write(compiled)
    # example: BOILERPLATE
