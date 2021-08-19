# This example is provided for informational purposes only and has not been audited for security.

from pyteal import *


def approval_program():
    on_creation = Seq(
        [
            Assert(Txn.application_args.length() == Int(1)),
            App.globalPut(Bytes("total supply"), Btoi(Txn.application_args[0])),
            App.globalPut(Bytes("reserve"), Btoi(Txn.application_args[0])),
            App.localPut(Int(0), Bytes("admin"), Int(1)),
            App.localPut(Int(0), Bytes("balance"), Int(0)),
            Return(Int(1)),
        ]
    )

    is_admin = App.localGet(Int(0), Bytes("admin"))

    on_closeout = Seq(
        [
            App.globalPut(
                Bytes("reserve"),
                App.globalGet(Bytes("reserve"))
                + App.localGet(Int(0), Bytes("balance")),
            ),
            Return(Int(1)),
        ]
    )

    register = Seq([App.localPut(Int(0), Bytes("balance"), Int(0)), Return(Int(1))])

    # configure the admin status of the account Txn.accounts[1]
    # sender must be admin
    new_admin_status = Btoi(Txn.application_args[1])
    set_admin = Seq(
        [
            Assert(And(is_admin, Txn.application_args.length() == Int(2))),
            App.localPut(Int(1), Bytes("admin"), new_admin_status),
            Return(Int(1)),
        ]
    )
    # NOTE: The above set_admin code is carefully constructed. If instead we used the following code:
    # Seq([
    #     Assert(Txn.application_args.length() == Int(2)),
    #     App.localPut(Int(1), Bytes("admin"), new_admin_status),
    #     Return(is_admin)
    # ])
    # It would be vulnerable to the following attack: a sender passes in their own address as
    # Txn.accounts[1], so then the line App.localPut(Int(1), Bytes("admin"), new_admin_status)
    # changes the sender's admin status, meaning the final Return(is_admin) can return anything the
    # sender wants. This allows anyone to become an admin!

    # move assets from the reserve to Txn.accounts[1]
    # sender must be admin
    mint_amount = Btoi(Txn.application_args[1])
    mint = Seq(
        [
            Assert(Txn.application_args.length() == Int(2)),
            Assert(mint_amount <= App.globalGet(Bytes("reserve"))),
            App.globalPut(
                Bytes("reserve"), App.globalGet(Bytes("reserve")) - mint_amount
            ),
            App.localPut(
                Int(1),
                Bytes("balance"),
                App.localGet(Int(1), Bytes("balance")) + mint_amount,
            ),
            Return(is_admin),
        ]
    )

    # transfer assets from the sender to Txn.accounts[1]
    transfer_amount = Btoi(Txn.application_args[1])
    transfer = Seq(
        [
            Assert(Txn.application_args.length() == Int(2)),
            Assert(transfer_amount <= App.localGet(Int(0), Bytes("balance"))),
            App.localPut(
                Int(0),
                Bytes("balance"),
                App.localGet(Int(0), Bytes("balance")) - transfer_amount,
            ),
            App.localPut(
                Int(1),
                Bytes("balance"),
                App.localGet(Int(1), Bytes("balance")) + transfer_amount,
            ),
            Return(Int(1)),
        ]
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_creation],
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(is_admin)],
        [Txn.on_completion() == OnComplete.UpdateApplication, Return(is_admin)],
        [Txn.on_completion() == OnComplete.CloseOut, on_closeout],
        [Txn.on_completion() == OnComplete.OptIn, register],
        [Txn.application_args[0] == Bytes("set admin"), set_admin],
        [Txn.application_args[0] == Bytes("mint"), mint],
        [Txn.application_args[0] == Bytes("transfer"), transfer],
    )

    return program


def clear_state_program():
    program = Seq(
        [
            App.globalPut(
                Bytes("reserve"),
                App.globalGet(Bytes("reserve"))
                + App.localGet(Int(0), Bytes("balance")),
            ),
            Return(Int(1)),
        ]
    )

    return program


if __name__ == "__main__":
    with open("asset_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=2)
        f.write(compiled)

    with open("asset_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=2)
        f.write(compiled)
