# using pyteal version 0.9.1

from pyteal import *

# Method selectors
create_method_selector = Bytes("base16", "43464101")
update_method_selector = Bytes("base16", "a0e81872")
optin_method_selector = Bytes("base16", "cfa68e36")
closeout_method_selector = Bytes("base16", "a9f42b3d")
delete_method_selector = Bytes("base16", "24378d3c")
add_method_selector = Bytes("base16", "fe6bdf69")
empty_method_selector = Bytes("base16", "a88c26a5")
payment_method_selector = Bytes("base16", "3e3b3d28")
reference_test_method_selector = Bytes("base16", "0df0050f")

return_event_selector = Bytes("base16", "151f7c75")

# Method signature should be: create(uint64)uint64
@Subroutine(TealType.none, "create(uint64)uint64")
def create(arg):
    return Log(Concat(return_event_selector, Itob(Btoi(arg) * Int(2))))


# Method signature should be: update()void
@Subroutine(TealType.none, "update()void")
def update():
    return Seq()


# Method signature should be: optIn(string)string
@Subroutine(TealType.none, "optIn(string)string")
def optIn(name):
    message = ScratchVar(TealType.bytes)
    return Seq(
        App.localPut(Int(0), Bytes("name"), Suffix(name, Int(2))),
        message.store(Concat(Bytes("hello "), App.localGet(Int(0), Bytes("name")))),
        Log(
            Concat(
                return_event_selector,
                Extract(Itob(Len(message.load())), Int(6), Int(2)),
                message.load(),
            )
        ),
    )


# Method signature should be: closeOut()string
@Subroutine(TealType.none, "closeOut()string")
def closeOut():
    message = ScratchVar(TealType.bytes)
    return Seq(
        message.store(Concat(Bytes("goodbye "), App.localGet(Int(0), Bytes("name")))),
        Log(
            Concat(
                return_event_selector,
                Extract(Itob(Len(message.load())), Int(6), Int(2)),
                message.load(),
            )
        ),
    )


# Method signature should be: delete()void
@Subroutine(TealType.none, "delete()void")
def deleteApp():
    return Assert(Txn.sender() == Global.creator_address())


# Method signature should be: add(uint64,uint64)uint64
@Subroutine(TealType.none, "add(uint64,uint64)uint64")
def add(a, b):
    # The app should log the first four bytes of the SHA512/256 hash of the word
    # "return" (0x151f7c75), followed by the method return argument.
    return Log(Concat(return_event_selector, Itob(Add(Btoi(a), Btoi(b)))))


# Method signature should be: empty()void
@Subroutine(TealType.none, "empty()void")
def empty():
    return Log(Bytes("random inconsequential log"))


# Method signature should be: payment(pay,uint64)bool
@Subroutine(TealType.none, "payment(pay,uint64)bool")
def payment(amount):
    prev = Txn.group_index() - Int(1)  # index of the pay transaction
    return Seq(
        Assert(Gtxn[prev].type_enum() == TxnType.Payment),
        Log(
            Concat(
                return_event_selector,
                If(Gtxn[prev].amount() == Btoi(amount))
                .Then(Bytes("base16", "80"))
                .Else(Bytes("base16", "00")),
            )
        ),
    )


# Method signature should be: referenceTest(account,application,account,asset,account,asset,asset,application,application)uint8[9]
@Subroutine(
    TealType.none,
    "referenceTest(account,application,account,asset,account,asset,asset,application,application)uint8[9]",
)
def referenceTest(
    account1,
    application1,
    account2,
    asset1,
    account3,
    asset2,
    asset3,
    application2,
    application3,
):
    return Log(
        Concat(
            return_event_selector,
            account1,
            account2,
            account3,
            application1,
            application2,
            application3,
            asset1,
            asset2,
            asset3,
        )
    )


def approval_program():
    program = (
        If(Txn.application_id() == Int(0))
        .Then(
            Seq(
                If(Txn.application_args.length() > Int(0)).Then(
                    Seq(
                        Assert(Txn.application_args[0] == create_method_selector),
                        create(Txn.application_args[1]),
                    )
                ),
                Approve(),
            )
        )
        .ElseIf(
            And(
                Txn.on_completion() == OnComplete.UpdateApplication,
                Txn.application_args[0] == update_method_selector,
            )
        )
        .Then(Seq(update(), Approve()))
        .ElseIf(
            And(
                Txn.on_completion() == OnComplete.OptIn,
                Txn.application_args[0] == optin_method_selector,
            )
        )
        .Then(Seq(optIn(Txn.application_args[1]), Approve()))
        .ElseIf(
            And(
                Txn.on_completion() == OnComplete.CloseOut,
                Txn.application_args[0] == closeout_method_selector,
            )
        )
        .Then(Seq(closeOut(), Approve()))
        .ElseIf(
            And(
                Txn.on_completion() == OnComplete.DeleteApplication,
                Txn.application_args[0] == delete_method_selector,
            )
        )
        .Then(Seq(deleteApp(), Approve()))
        .ElseIf(
            And(  # calling the add method
                Txn.on_completion() == OnComplete.NoOp,
                Txn.application_args[0] == add_method_selector,
            )
        )
        .Then(Seq(add(Txn.application_args[1], Txn.application_args[2]), Approve()))
        .ElseIf(
            And(  # calling the empty method
                Txn.on_completion() == OnComplete.NoOp,
                Txn.application_args[0] == empty_method_selector,
            )
        )
        .Then(Seq(empty(), Approve()))
        .ElseIf(
            And(  # calling the payment method
                Txn.on_completion() == OnComplete.NoOp,
                Txn.application_args[0] == payment_method_selector,
            )
        )
        .Then(Seq(payment(Txn.application_args[1]), Approve()))
        .ElseIf(
            And(  # calling the accountReference method
                Txn.on_completion() == OnComplete.NoOp,
                Txn.application_args[0] == reference_test_method_selector,
            )
        )
        .Then(
            Seq(
                referenceTest(
                    Txn.application_args[1],
                    Txn.application_args[2],
                    Txn.application_args[3],
                    Txn.application_args[4],
                    Txn.application_args[5],
                    Txn.application_args[6],
                    Txn.application_args[7],
                    Txn.application_args[8],
                    Txn.application_args[9],
                ),
                Approve(),
            )
        )
        .Else(Reject())
    )
    return program


if __name__ == "__main__":
    import os

    path = os.path.dirname(__file__)

    with open(os.path.join(path, "abi_method_call.teal"), "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=5)
        f.write(compiled)
