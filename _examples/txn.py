from pyteal import (
    Approve,
    Assert,
    Btoi,
    Bytes,
    Global,
    Gtxn,
    If,
    Int,
    Mode,
    OnComplete,
    Reject,
    Txn,
    TxnType,
    compileTeal,
)


def on_complete():
    # example: TXN_ONCOMPLETE
    program = OnComplete.NoOp == Txn.on_completion()
    print(compileTeal(program, Mode.Application))
    # example: TXN_ONCOMPLETE


def app_args():
    # example: TXN_APP_ARGS
    program = Txn.application_args[1] == Bytes("claim")
    print(compileTeal(program, Mode.Application))
    # example: TXN_APP_ARGS


def num_app_args():
    # example: TXN_NUM_APP_ARGS
    program = Txn.application_args.length() == Int(4)
    print(compileTeal(program, Mode.Application))
    # example: TXN_NUM_APP_ARGS


def arg_to_int():
    # example: TXN_APP_ARG_TO_INT
    program = Btoi(Txn.application_args[0])
    print(compileTeal(program, Mode.Application))
    # example: TXN_APP_ARG_TO_INT


def txn_amt():
    # example: TXN_AMOUNT
    program = Txn.amount()
    print(compileTeal(program, Mode.Application))
    # example: TXN_AMOUNT


def group_size():
    # example: TXN_GROUP_SIZE
    program = Global.group_size() == Int(2)
    print(compileTeal(program, Mode.Application))
    # example: TXN_GROUP_SIZE


def gtxn_type_enum():
    # example: GTXN_TYPE_ENUM
    program = Gtxn[1].type_enum() == TxnType.Payment
    print(compileTeal(program, Mode.Application))
    # example: GTXN_TYPE_ENUM


def gtxn_app_args():
    # example: GTXN_APP_ARGS
    program = Gtxn[Txn.group_index() - Int(1)].application_args[0]
    print(compileTeal(program, Mode.Application))
    # example: GTXN_APP_ARGS


def app_call():
    # example: APPL_CALL
    # this would approve _ANY_ transaction that has its
    # first app arg set to the byte string "myparam"
    # and reject all others
    program = If(Bytes("myparm") == Txn.application_args[0], Approve(), Reject())
    print(compileTeal(program, Mode.Application))
    # example: APPL_CALL


def app_update():
    # example: APPL_UPDATE
    program = Assert(
        Txn.on_completion() == OnComplete.UpdateApplication,
        Global.creator_address() == Txn.sender(),
    )
    print(compileTeal(program, Mode.Application))
    # example: APPL_UPDATE


def app_update_reject():
    # example: APPL_UPDATE_REJECT
    program = If(
        OnComplete.UpdateApplication == Txn.on_completion(),
        Reject(),
        # placeholder, update with actual logic
        Approve(),
    )
    print(compileTeal(program, Mode.Application))
    # example: APPL_UPDATE_REJECT


def is_opt_in():
    # example: APPL_OPTIN
    # this would reject _ANY_ transaction that isn't an opt-in
    # and approve _ANY_ transaction that is an opt-in
    program = If(OnComplete.OptIn == Txn.on_completion(), Approve(), Reject())
    print(compileTeal(program, Mode.Application))
    # example: APPL_OPTIN
