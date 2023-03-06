from pyteal import App, Bytes, If, Int, Mode, Return, Seq, Txn, compileTeal


def write_to_global_state():
    # example: WRITE_GLOBAL_STATE
    program = App.globalPut(Bytes("Mykey"), Int(50))
    print(compileTeal(program, Mode.Application))
    # example: WRITE_GLOBAL_STATE


def write_sender_local_state():
    # example: WRITE_SENDER_LOCAL_STATE
    program = App.localPut(Int(0), Bytes("MyLocalKey"), Int(50))
    print(compileTeal(program, Mode.Application))
    # example: WRITE_SENDER_LOCAL_STATE


def write_other_local_state():
    # example: WRITE_OTHER_LOCAL_STATE
    program = App.localPut(Int(2), Bytes("MyLocalKey"), Int(50))
    print(compileTeal(program, Mode.Application))
    # example: WRITE_OTHER_LOCAL_STATE


def read_global_state():
    # example: READ_GLOBAL_STATE
    program = App.globalGet(Bytes("MyGlobalKey"))
    print(compileTeal(program, Mode.Application))
    # example: READ_GLOBAL_STATE


def read_local_state():
    # example: READ_LOCAL_STATE
    program = App.localGet(Int(0), Bytes("MyLocalKey"))
    print(compileTeal(program, Mode.Application))
    # example: READ_LOCAL_STATE


def read_sender_local_state_external():
    # example: READ_SENDER_LOCAL_STATE_EX
    program = App.localGetEx(Int(0), Txn.application_id(), Bytes("MyAmountGiven"))
    print(compileTeal(program, Mode.Application))
    # example: READ_SENDER_LOCAL_STATE_EX


def read_local_state_external():
    # example: READ_LOCAL_STATE_EX
    get_amount_given = App.localGetEx(
        Int(0), Txn.application_id(), Bytes("MyAmountGiven")
    )

    # Change these to appropriate logic for new and previous givers.
    new_giver_logic = Seq(Return(Int(1)))

    previous_giver_logic = Seq(Return(Int(1)))

    program = Seq(
        get_amount_given,
        If(get_amount_given.hasValue(), previous_giver_logic, new_giver_logic),
    )

    print(compileTeal(program, Mode.Application))
    # example: READ_LOCAL_STATE_EX


def read_global_state_external():
    # example: READ_GLOBAL_STATE_EX
    get_global_key = App.globalGetEx(Int(0), Bytes("MyGlobalKey"))

    # Update with appropriate logic for use case
    increment_existing = Seq(Return(Int(1)))

    program = Seq(
        get_global_key,
        If(get_global_key.hasValue(), increment_existing, Return(Int(1))),
    )

    print(compileTeal(program, Mode.Application))
    # example: READ_GLOBAL_STATE_EX
