# This example is provided for informational purposes only and has not been audited for security.
from pyteal import *
import json


def on_delete() -> Expr:
    return Assert(Txn.sender() == Global.creator_address())


router = Router(
    name="OpenPollingApp",
    descr="This is a polling application with no restrictions on who can participate.",
    bare_calls=BareCallActions(
        delete_application=OnCompleteAction.call_only(on_delete())
    ),
)


@router.method(no_op=CallConfig.CREATE)
def create(options: abi.DynamicArray[abi.String], can_resubmit: abi.Bool) -> Expr:
    """Create a new polling application.

    Args:
        options: A list of options for the poll. This list should not contain duplicate entries.
        resubmission: A boolean value indicating whether this poll allows accounts to change their
            answer after their first submission.
        can_resubmit: Whether this poll allows accounts to change their submissions or not.
    """
    return Seq()


@router.method(name="open")
def open_poll() -> Expr:
    """Marks this poll as open.

    This will fail if the poll is already open.

    The poll must be open in order to receive user input.
    """
    return Seq()


@router.method(name="close")
def close_poll() -> Expr:
    """Marks this poll as closed.

    This will fail if the poll is already closed.
    """
    return Seq()


@router.method
def submit(choice: abi.Uint16) -> Expr:
    """Submit a response to the poll.

    Submissions can only be received if the poll is open. If the poll is closed, this will fail.

    If a submission has already been made by the sender and the poll allows resubmissions, the
    sender's choice will be updated to the most recent submission. If the poll does not allow
    resubmissions, this action will fail.

    Args:
        choice: The choice made by the sender. This must be an index into the options for this poll.
    """
    return Seq()


class PollStatus(abi.NamedTuple):
    can_resubmit: abi.Field[abi.Bool]
    is_open: abi.Field[abi.Bool]
    results: abi.Field[abi.DynamicArray[abi.Tuple2[abi.String, abi.Uint64]]]


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
    results = abi.make(abi.DynamicArray[abi.Tuple2[abi.String, abi.Uint64]])
    return Seq(
        can_resubmit.set(False),
        is_open.set(False),
        results.set([]),
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
