# This example is provided for informational purposes only and has not been audited for security.

from pyteal import *

def approval_program():
    on_creation = Seq([
        App.globalPut(Bytes("Creator"), Txn.sender()),
        Assert(Txn.application_args.length() == Int(4)),
        App.globalPut(Bytes("RegBegin"), Btoi(Txn.application_args[0])),
        App.globalPut(Bytes("RegEnd"), Btoi(Txn.application_args[1])),
        App.globalPut(Bytes("VoteBegin"), Btoi(Txn.application_args[2])),
        App.globalPut(Bytes("VoteEnd"), Btoi(Txn.application_args[3])),
        Return(Int(1))
    ])

    is_creator = Txn.sender() == App.globalGet(Bytes("Creator"))

    get_vote = App.localGetEx(Int(0), Txn.application_id(), Bytes("voted"))
    get_count = App.globalGetEx(Int(0), get_vote.value())

    decrement_existing = Seq([
        App.globalPut(get_vote.value(), get_count.value() - Int(1)),
        Return(Int(1))
    ])

    if_voted = Seq([
        get_count,
        If(get_count.hasValue(), decrement_existing, Return(Int(1)))
    ])

    on_closeout = If(
        Global.round() > App.globalGet(Bytes("VoteEnd")),
        Return(Int(1)),
        Seq([
            get_vote,
            If(get_vote.hasValue(), if_voted, Return(Int(1)))
        ])
    )

    on_register = Return(And(
        Global.round() >= App.globalGet(Bytes("RegBegin")),
        Global.round() <= App.globalGet(Bytes("RegEnd"))
    ))

    get_candidate = App.globalGetEx(Int(0), Txn.application_args[1])

    not_voted = Seq([
        get_candidate,
        App.globalPut(Txn.application_args[1], If(get_candidate.hasValue(), get_candidate.value() + Int(1), Int(1))),
        App.localPut(Int(0), Bytes("voted"), Txn.application_args[1]),
        Return(Int(1))
    ])

    on_vote = Seq([
        Assert(And(Global.round() >= App.globalGet(Bytes("VoteBegin")), Global.round() <= App.globalGet(Bytes("VoteEnd")))),
        get_vote,
        If(get_vote.hasValue(), Return(Int(1)), not_voted)
    ])

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(is_creator)],
        [Txn.on_completion() == OnComplete.CloseOut, on_closeout],
        [Txn.on_completion() == OnComplete.OptIn, on_register],
        [Bytes("vote") == Txn.application_args[0], on_vote]
    )

    return program

def close_out_program():
    get_voted = App.localGetEx(Int(0), Txn.application_id(), Bytes("voted"))
    get_candidate = App.globalGetEx(Int(0), get_voted.value())

    decrement_existing = Seq([
        App.globalPut(get_voted.value(), get_candidate.value() - Int(1)),
        Return(Int(1))
    ])

    voted = Seq([
        get_candidate,
        If(get_candidate.hasValue(), decrement_existing, Return(Int(1)))
    ])

    program = If(
        Global.round() > App.globalGet(Bytes("VoteEnd")),
        Return(Int(1)),
        Seq([
            get_voted,
            If(get_voted.hasValue(), voted, Return(Int(1)))
        ])
    )

    return program

with open('vote_approval.teal', 'w') as f:
    compiled = compileTeal(approval_program(), Mode.Application)
    f.write(compiled)

with open('vote_close_out.teal', 'w') as f:
    compiled = compileTeal(close_out_program(), Mode.Application)
    f.write(compiled)
