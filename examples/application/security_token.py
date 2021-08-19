# This example is provided for informational purposes only and has not been audited for security.

from pyteal import *


def approval_program():
    on_creation = Seq(
        [
            Assert(Txn.application_args.length() == Int(1)),
            App.globalPut(Bytes("total supply"), Btoi(Txn.application_args[0])),
            App.globalPut(Bytes("reserve"), Btoi(Txn.application_args[0])),
            App.globalPut(Bytes("paused"), Int(0)),
            App.localPut(Int(0), Bytes("contract admin"), Int(1)),
            App.localPut(Int(0), Bytes("transfer admin"), Int(1)),
            App.localPut(Int(0), Bytes("balance"), Int(0)),
            Return(Int(1)),
        ]
    )

    is_contract_admin = App.localGet(Int(0), Bytes("contract admin"))
    is_transfer_admin = App.localGet(Int(0), Bytes("transfer admin"))
    is_any_admin = is_contract_admin.Or(is_transfer_admin)

    can_delete = And(
        is_contract_admin,
        App.globalGet(Bytes("total supply")) == App.globalGet(Bytes("reserve")),
    )

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

    # pause all transfers
    # sender must be any admin
    new_pause_value = Btoi(Txn.application_args[1])
    pause = Seq(
        [
            Assert(Txn.application_args.length() == Int(2)),
            App.globalPut(Bytes("paused"), new_pause_value),
            Return(is_any_admin),
        ]
    )

    # configure the admin status of the account Txn.accounts[1]
    # sender must be contract admin
    new_admin_type = Txn.application_args[1]
    new_admin_status = Btoi(Txn.application_args[2])
    set_admin = Seq(
        [
            Assert(
                And(
                    is_contract_admin,
                    Txn.application_args.length() == Int(3),
                    Or(
                        new_admin_type == Bytes("contract admin"),
                        new_admin_type == Bytes("transfer admin"),
                    ),
                    Txn.accounts.length() == Int(1),
                )
            ),
            App.localPut(Int(1), new_admin_type, new_admin_status),
            Return(Int(1)),
        ]
    )
    # NOTE: The above set_admin code is carefully constructed. If instead we used the following code:
    # Seq([
    #     Assert(And(
    #         Txn.application_args.length() == Int(3),
    #         Or(new_admin_type == Bytes("contract admin"), new_admin_type == Bytes("transfer admin")),
    #         Txn.accounts.length() == Int(1)
    #     )),
    #     App.localPut(Int(1), new_admin_type, new_admin_status),
    #     Return(is_contract_admin)
    # ])
    # It would be vulnerable to the following attack: a sender passes in their own address as
    # Txn.accounts[1], so then the line App.localPut(Int(1), new_admin_type, new_admin_status)
    # changes the sender's admin status, meaning the final Return(is_contract_admin) can return
    # anything the sender wants. This allows anyone to become an admin!

    # freeze Txn.accounts[1]
    # sender must be any admin
    new_freeze_value = Btoi(Txn.application_args[1])
    freeze = Seq(
        [
            Assert(
                And(
                    Txn.application_args.length() == Int(2),
                    Txn.accounts.length() == Int(1),
                )
            ),
            App.localPut(Int(1), Bytes("frozen"), new_freeze_value),
            Return(is_any_admin),
        ]
    )

    # modify the max balance of Txn.accounts[1]
    # if max_balance_value is 0, will delete the existing max balance limitation on the account
    # sender must be transfer admin
    max_balance_value = Btoi(Txn.application_args[1])
    max_balance = Seq(
        [
            Assert(
                And(
                    Txn.application_args.length() == Int(2),
                    Txn.accounts.length() == Int(1),
                )
            ),
            If(
                max_balance_value == Int(0),
                App.localDel(Int(1), Bytes("max balance")),
                App.localPut(Int(1), Bytes("max balance"), max_balance_value),
            ),
            Return(is_transfer_admin),
        ]
    )

    # lock Txn.accounts[1] until a UNIX timestamp
    # sender must be transfer admin
    lock_until_value = Btoi(Txn.application_args[1])
    lock_until = Seq(
        [
            Assert(
                And(
                    Txn.application_args.length() == Int(2),
                    Txn.accounts.length() == Int(1),
                )
            ),
            If(
                lock_until_value == Int(0),
                App.localDel(Int(1), Bytes("lock until")),
                App.localPut(Int(1), Bytes("lock until"), lock_until_value),
            ),
            Return(is_transfer_admin),
        ]
    )

    set_transfer_group = Seq(
        [
            Assert(
                And(
                    Txn.application_args.length() == Int(3),
                    Txn.accounts.length() == Int(1),
                )
            ),
            App.localPut(
                Int(1), Bytes("transfer group"), Btoi(Txn.application_args[2])
            ),
        ]
    )

    def getRuleKey(sendGroup, receiveGroup):
        return Concat(Bytes("rule"), Itob(sendGroup), Itob(receiveGroup))

    lock_transfer_key = getRuleKey(
        Btoi(Txn.application_args[2]), Btoi(Txn.application_args[3])
    )
    lock_transfer_until = Btoi(Txn.application_args[4])
    lock_transfer_group = Seq(
        [
            Assert(Txn.application_args.length() == Int(5)),
            If(
                lock_transfer_until == Int(0),
                App.globalDel(lock_transfer_key),
                App.globalPut(lock_transfer_key, lock_transfer_until),
            ),
        ]
    )

    # sender must be transfer admin
    transfer_group = Seq(
        [
            Assert(Txn.application_args.length() > Int(2)),
            Cond(
                [Txn.application_args[1] == Bytes("set"), set_transfer_group],
                [Txn.application_args[1] == Bytes("lock"), lock_transfer_group],
            ),
            Return(is_transfer_admin),
        ]
    )

    # move assets from the reserve to Txn.accounts[1]
    # sender must be contract admin
    mint_amount = Btoi(Txn.application_args[1])
    mint = Seq(
        [
            Assert(
                And(
                    Txn.application_args.length() == Int(2),
                    Txn.accounts.length() == Int(1),
                    mint_amount <= App.globalGet(Bytes("reserve")),
                )
            ),
            App.globalPut(
                Bytes("reserve"), App.globalGet(Bytes("reserve")) - mint_amount
            ),
            App.localPut(
                Int(1),
                Bytes("balance"),
                App.localGet(Int(1), Bytes("balance")) + mint_amount,
            ),
            Return(is_contract_admin),
        ]
    )

    # move assets from Txn.accounts[1] to the reserve
    # sender must be contract admin
    burn_amount = Btoi(Txn.application_args[1])
    burn = Seq(
        [
            Assert(
                And(
                    Txn.application_args.length() == Int(2),
                    Txn.accounts.length() == Int(1),
                    burn_amount <= App.localGet(Int(1), Bytes("balance")),
                )
            ),
            App.globalPut(
                Bytes("reserve"), App.globalGet(Bytes("reserve")) + burn_amount
            ),
            App.localPut(
                Int(1),
                Bytes("balance"),
                App.localGet(Int(1), Bytes("balance")) - burn_amount,
            ),
            Return(is_contract_admin),
        ]
    )

    # transfer assets from the sender to Txn.accounts[1]
    transfer_amount = Btoi(Txn.application_args[1])
    receiver_max_balance = App.localGetEx(Int(1), App.id(), Bytes("max balance"))
    transfer = Seq(
        [
            Assert(
                And(
                    Txn.application_args.length() == Int(2),
                    Txn.accounts.length() == Int(1),
                    transfer_amount <= App.localGet(Int(0), Bytes("balance")),
                )
            ),
            receiver_max_balance,
            If(
                Or(
                    App.globalGet(Bytes("paused")),
                    App.localGet(Int(0), Bytes("frozen")),
                    App.localGet(Int(1), Bytes("frozen")),
                    App.localGet(Int(0), Bytes("lock until"))
                    >= Global.latest_timestamp(),
                    App.localGet(Int(1), Bytes("lock until"))
                    >= Global.latest_timestamp(),
                    App.globalGet(
                        getRuleKey(
                            App.localGet(Int(0), Bytes("transfer group")),
                            App.localGet(Int(1), Bytes("transfer group")),
                        )
                    )
                    >= Global.latest_timestamp(),
                    And(
                        receiver_max_balance.hasValue(),
                        receiver_max_balance.value()
                        < App.localGet(Int(1), Bytes("balance")) + transfer_amount,
                    ),
                ),
                Return(Int(0)),
            ),
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
        [Txn.on_completion() == OnComplete.DeleteApplication, Return(can_delete)],
        [
            Txn.on_completion() == OnComplete.UpdateApplication,
            Return(is_contract_admin),
        ],
        [Txn.on_completion() == OnComplete.CloseOut, on_closeout],
        [Txn.on_completion() == OnComplete.OptIn, register],
        [Txn.application_args[0] == Bytes("pause"), pause],
        [Txn.application_args[0] == Bytes("set admin"), set_admin],
        [Txn.application_args[0] == Bytes("freeze"), freeze],
        [Txn.application_args[0] == Bytes("max balance"), max_balance],
        [Txn.application_args[0] == Bytes("lock until"), lock_until],
        [Txn.application_args[0] == Bytes("transfer group"), transfer_group],
        [Txn.application_args[0] == Bytes("mint"), mint],
        [Txn.application_args[0] == Bytes("burn"), burn],
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
    with open("security_token_approval.teal", "w") as f:
        compiled = compileTeal(approval_program(), mode=Mode.Application, version=2)
        f.write(compiled)

    with open("security_token_clear_state.teal", "w") as f:
        compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=2)
        f.write(compiled)
