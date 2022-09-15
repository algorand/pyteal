# This example is provided for informational purposes only and has not been audited for security.
from pyteal import *
import json


@Subroutine(TealType.none)
def assert_sender_is_creator() -> Expr:
    return Assert(Txn.sender() == Global.creator_address())


# move any balance that the user has into the "lost" amount when they close out or clear state
transfer_balance_to_lost = App.globalPut(
    Bytes("lost"),
    App.globalGet(Bytes("lost")) + App.localGet(Txn.sender(), Bytes("balance")),
)

router = Router(
    name="AlgoBank",
    bare_calls=BareCallActions(
        # approve a creation no-op call
        no_op=OnCompleteAction(action=Approve(), call_config=CallConfig.CREATE),
        # approve opt-in calls during normal usage, and during creation as a convenience for the creator
        opt_in=OnCompleteAction(action=Approve(), call_config=CallConfig.ALL),
        # move any balance that the user has into the "lost" amount when they close out or clear state
        close_out=OnCompleteAction(
            action=transfer_balance_to_lost, call_config=CallConfig.CALL
        ),
        clear_state=OnCompleteAction(
            action=transfer_balance_to_lost, call_config=CallConfig.CALL
        ),
        # only the creator can update or delete the app
        update_application=OnCompleteAction(
            action=assert_sender_is_creator, call_config=CallConfig.CALL
        ),
        delete_application=OnCompleteAction(
            action=assert_sender_is_creator, call_config=CallConfig.CALL
        ),
    ),
)


@router.method(no_op=CallConfig.CALL, opt_in=CallConfig.CALL)
def deposit(payment: abi.PaymentTransaction, sender: abi.Account) -> Expr:
    """This method receives a payment from an account opted into this app and records it as a deposit.

    The caller may opt into this app during this call.

    Args:
        payment: A payment transaction containing the amount of Algos the user wishes to deposit.
            The receiver of this transaction must be this app's escrow account.
        sender: An account that is opted into this app (or will opt in during this method call).
            The deposited funds will be recorded in this account's local state. This account must
            be the same as the sender of the `payment` transaction.
    """
    return Seq(
        Assert(payment.get().sender() == sender.address()),
        Assert(payment.get().receiver() == Global.current_application_address()),
        App.localPut(
            sender.address(),
            Bytes("balance"),
            App.localGet(sender.address(), Bytes("balance")) + payment.get().amount(),
        ),
    )


@router.method
def getBalance(user: abi.Account, *, output: abi.Uint64) -> Expr:
    """Lookup the balance of a user held by this app.

    Args:
        user: The user whose balance you wish to look up. This user must be opted into this app.

    Returns:
        The balance corresponding to the given user, in microAlgos.
    """
    return output.set(App.localGet(user.address(), Bytes("balance")))


@router.method
def withdraw(amount: abi.Uint64, recipient: abi.Account) -> Expr:
    """Withdraw an amount of Algos held by this app.

    The sender of this method call will be the source of the Algos, and the destination will be
    the `recipient` argument.

    The Algos will be transferred to the recipient using an inner transaction whose fee is set
    to 0, meaning the caller's transaction must include a surplus fee to cover the inner
    transaction.

    Args:
        amount: The amount of Algos requested to be withdraw, in microAlgos. This method will fail
            if this amount exceeds the amount of Algos held by this app for the method call sender.
        recipient: An account who will receive the withdrawn Algos. This may or may not be the same
            as the method call sender.
    """
    return Seq(
        # if amount is larger than App.localGet(Txn.sender(), Bytes("balance")), the subtraction
        # will underflow and fail this method call
        App.localPut(
            Txn.sender(),
            Bytes("balance"),
            App.localGet(Txn.sender(), Bytes("balance")) - amount.get(),
        ),
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.Payment,
                TxnField.receiver: recipient.address(),
                TxnField.amount: amount.get(),
                TxnField.fee: Int(0),
            }
        ),
        InnerTxnBuilder.Submit(),
    )


approval_program, clear_state_program, contract = router.compile_program(
    version=6, optimize=OptimizeOptions(scratch_slots=True)
)

if __name__ == "__main__":
    with open("algobank_approval.teal", "w") as f:
        f.write(approval_program)

    with open("algobank_clear_state.teal", "w") as f:
        f.write(clear_state_program)

    with open("algobank.json", "w") as f:
        f.write(json.dumps(contract.dictify(), indent=4))
