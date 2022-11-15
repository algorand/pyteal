# This example is provided for informational purposes only and has not been audited for security.
import json
from typing import Literal
from pyteal import *


def on_delete() -> Expr:
    return Assert(Txn.sender() == Global.creator_address())


router = Router(
    name="OpenPollingApp",
    descr="A polling application with no restrictions on who can participate.",
    bare_calls=BareCallActions(
        delete_application=OnCompleteAction.call_only(on_delete())
    ),
)

open_key = Bytes(b"open")
resubmit_key = Bytes(b"resubmit")
option_name_prefix = b"option_name_"
option_name_keys = [
    Bytes(option_name_prefix + b"\x00"),
    Bytes(option_name_prefix + b"\x01"),
    Bytes(option_name_prefix + b"\x02"),
]
option_count_prefix = b"option_count_"
option_count_keys = [
    Bytes(option_count_prefix + b"\x00"),
    Bytes(option_count_prefix + b"\x01"),
    Bytes(option_count_prefix + b"\x02"),
]


@router.method(no_op=CallConfig.CREATE)
def create(
    options: abi.StaticArray[abi.String, Literal[3]], can_resubmit: abi.Bool
) -> Expr:
    """Create a new polling application.

    Args:
        options: A list of options for the poll. This list should not contain duplicate entries.
        can_resubmit: Whether this poll allows accounts to change their submissions or not.
    """
    return Seq(
        App.globalPut(open_key, Int(0)),
        App.globalPut(resubmit_key, can_resubmit.get()),
        App.globalPut(option_name_keys[0], options[0].use(lambda value: value.get())),
        App.globalPut(option_count_keys[0], Int(0)),
        App.globalPut(option_name_keys[1], options[1].use(lambda value: value.get())),
        App.globalPut(option_count_keys[1], Int(0)),
        App.globalPut(option_name_keys[2], options[2].use(lambda value: value.get())),
        App.globalPut(option_count_keys[2], Int(0)),
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
        Assert(choice.get() < Int(3)),
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
    can_resubmit: abi.Field[abi.Bool]
    is_open: abi.Field[abi.Bool]
    results: abi.Field[abi.StaticArray[abi.Tuple2[abi.String, abi.Uint64], Literal[3]]]


@router.method
def status(*, output: PollStatus) -> Expr:
    """Get the status of this poll.

    Returns:
        A tuple containing the following information, in order: whether the poll allows
        resubmission, whether the poll is open, and an array of the poll's current results. This
        array contains one entry per option, and each entry is a tuple of that option's value and
        the number of accounts who have voted for it.
    """
    can_resubmit = abi.make(abi.Bool)
    is_open = abi.make(abi.Bool)
    option_name = abi.make(abi.String)
    option_count = abi.make(abi.Uint64)
    partial_results = [
        abi.make(abi.Tuple2[abi.String, abi.Uint64]),
        abi.make(abi.Tuple2[abi.String, abi.Uint64]),
        abi.make(abi.Tuple2[abi.String, abi.Uint64]),
    ]
    results = abi.make(abi.StaticArray[abi.Tuple2[abi.String, abi.Uint64], Literal[3]])
    return Seq(
        can_resubmit.set(App.globalGet(resubmit_key)),
        is_open.set(App.globalGet(open_key)),
        option_name.set(App.globalGet(option_name_keys[0])),
        option_count.set(App.globalGet(option_count_keys[0])),
        partial_results[0].set(option_name, option_count),
        option_name.set(App.globalGet(option_name_keys[1])),
        option_count.set(App.globalGet(option_count_keys[1])),
        partial_results[1].set(option_name, option_count),
        option_name.set(App.globalGet(option_name_keys[2])),
        option_count.set(App.globalGet(option_count_keys[2])),
        partial_results[2].set(option_name, option_count),
        results.set([partial_results[0], partial_results[1], partial_results[2]]),
        output.set(can_resubmit, is_open, results),
    )


approval_program, clear_state_program, contract = router.compile_program(
    version=8, optimize=OptimizeOptions(scratch_slots=True)
)

if __name__ == "__main__":
    with open("approval.teal", "w") as f:
        f.write(approval_program)

    with open("clear_state.teal", "w") as f:
        f.write(clear_state_program)

    with open("contract.json", "w") as f:
        f.write(json.dumps(contract.dictify(), indent=4))
