# This example is provided for informational purposes only and has not been audited for security.
# import json
from typing import Literal
from pyteal import *


pragma(compiler_version=">0.19.0")

on_delete = Seq(
    Assert(Txn.sender() == Global.creator_address()),
    InnerTxnBuilder.Execute(
        {
            TxnField.type_enum: TxnType.Payment,
            TxnField.close_remainder_to: Txn.sender(),
        }
    ),
)


router = Router(
    name="OpenPollingApp",
    descr="A polling application with no restrictions on who can participate.",
    bare_calls=BareCallActions(
        delete_application=OnCompleteAction.call_only(on_delete)
    ),
)

NUM_OPTIONS = 7

open_key = Bytes(b"open")
resubmit_key = Bytes(b"resubmit")
question_key = Bytes(b"question")
option_name_prefix = b"option_name_"
option_name_keys = [Bytes(option_name_prefix + bytes([i])) for i in range(NUM_OPTIONS)]
option_count_prefix = b"option_count_"
option_count_keys = [
    Bytes(option_count_prefix + bytes([i])) for i in range(NUM_OPTIONS)
]


@router.method(no_op=CallConfig.CREATE)
def create(
    question: abi.String, options: abi.StaticArray[abi.String, Literal[NUM_OPTIONS]], can_resubmit: abi.Bool  # type: ignore
) -> Expr:
    """Create a new polling application.

    Args:
        question: The question this poll is asking.
        options: A list of options for the poll. This list should not contain duplicate entries.
        can_resubmit: Whether this poll allows accounts to change their submissions or not.
    """
    name = abi.make(abi.String)
    return Seq(
        App.globalPut(open_key, Int(0)),
        App.globalPut(resubmit_key, can_resubmit.get()),
        App.globalPut(question_key, question.get()),
        *[
            Seq(
                name.set(options[i]),
                App.globalPut(option_name_keys[i], name.get()),
                App.globalPut(option_count_keys[i], Int(0)),
            )
            for i in range(NUM_OPTIONS)
        ],
    )


@router.method(name="open")
def open_poll() -> Expr:
    """Marks this poll as open.

    This will fail if the poll is already open.

    The poll must be open in order to receive user input.
    """
    return Seq(
        Assert(Not(App.globalGet(open_key))),
        App.globalPut(open_key, Int(1)),
    )


@router.method(name="close")
def close_poll() -> Expr:
    """Marks this poll as closed.

    This will fail if the poll is already closed.
    """
    return Seq(
        Assert(App.globalGet(open_key)),
        App.globalPut(open_key, Int(0)),
    )


@router.method
def submit(choice: abi.Uint8) -> Expr:
    """Submit a response to the poll.

    Submissions can only be received if the poll is open. If the poll is closed, this will fail.

    If a submission has already been made by the sender and the poll allows resubmissions, the
    sender's choice will be updated to the most recent submission. If the poll does not allow
    resubmissions, this action will fail.

    Args:
        choice: The choice made by the sender. This must be an index into the options for this poll.
    """
    new_choice_count_key = ScratchVar(TealType.bytes)
    old_choice_count_key = ScratchVar(TealType.bytes)
    return Seq(
        Assert(choice.get() < Int(NUM_OPTIONS)),
        new_choice_count_key.store(
            SetByte(option_count_keys[0], Int(len(option_count_prefix)), choice.get())
        ),
        sender_box := App.box_get(Txn.sender()),
        If(sender_box.hasValue()).Then(
            # the sender has already submitted a response, so it must be cleared
            Assert(App.globalGet(resubmit_key)),
            old_choice_count_key.store(
                SetByte(
                    option_count_keys[0],
                    Int(len(option_count_prefix)),
                    Btoi(sender_box.value()),
                )
            ),
            App.globalPut(
                old_choice_count_key.load(),
                App.globalGet(old_choice_count_key.load()) - Int(1),
            ),
        ),
        App.box_put(Txn.sender(), choice.encode()),
        App.globalPut(
            new_choice_count_key.load(),
            App.globalGet(new_choice_count_key.load()) + Int(1),
        ),
    )


class PollStatus(abi.NamedTuple):
    question: abi.Field[abi.String]
    can_resubmit: abi.Field[abi.Bool]
    is_open: abi.Field[abi.Bool]
    results: abi.Field[abi.StaticArray[abi.Tuple2[abi.String, abi.Uint64], Literal[NUM_OPTIONS]]]  # type: ignore


@router.method
def status(*, output: PollStatus) -> Expr:
    """Get the status of this poll.

    Returns:
        A tuple containing the following information, in order: the question is poll is asking,
        whether the poll allows resubmission, whether the poll is open, and an array of the poll's
        current results. This array contains one entry per option, and each entry is a tuple of that
        option's value and the number of accounts who have voted for it.
    """
    question = abi.make(abi.String)
    can_resubmit = abi.make(abi.Bool)
    is_open = abi.make(abi.Bool)
    option_name = abi.make(abi.String)
    option_count = abi.make(abi.Uint64)
    partial_results = [
        abi.make(abi.Tuple2[abi.String, abi.Uint64]) for i in range(NUM_OPTIONS)
    ]
    results = abi.make(abi.StaticArray[abi.Tuple2[abi.String, abi.Uint64], Literal[NUM_OPTIONS]])  # type: ignore
    return Seq(
        question.set(App.globalGet(question_key)),
        can_resubmit.set(App.globalGet(resubmit_key)),
        is_open.set(App.globalGet(open_key)),
        *[
            Seq(
                option_name.set(App.globalGet(option_name_keys[i])),
                option_count.set(App.globalGet(option_count_keys[i])),
                partial_results[i].set(option_name, option_count),
            )
            for i in range(NUM_OPTIONS)
        ],
        results.set(partial_results),
        output.set(question, can_resubmit, is_open, results),
    )


if __name__ == "__main__":
    bundle = router.compile(
        version=8,
        assemble_constants=False,
        optimize=OptimizeOptions(scratch_slots=True, frame_pointers=True),
        with_sourcemaps=True,
        pcs_in_sourcemap=True,
        annotate_teal=True,
        annotate_teal_headers=True,
        annotate_teal_concise=True,
    )
    print(bundle.approval_annotated_teal)


# approval_program, clear_state_program, contract = router.compile_program(
#     version=8, optimize=OptimizeOptions(scratch_slots=True)
# )

# if __name__ == "__main__":
#     with open("decipher_approval.teal", "w") as f:
#         f.write(approval_program)

#     with open("decipher_clear.teal", "w") as f:
#         f.write(clear_state_program)

#     with open("decipher.json", "w") as f:
#         f.write(json.dumps(contract.dictify(), indent=4))
