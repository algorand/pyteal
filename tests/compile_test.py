import os
from pyteal import *
from pyteal.util import reset_label_count

def test_basic_bank():
    from examples.signature.basic import bank_for_account

    program = bank_for_account("ZZAF5ARA4MEC5PVDOP64JM5O5MQST63Q2KOY2FLYFLXXD3PFSNJJBYAFZM")

    target_path = os.path.join(os.path.dirname(__file__), "../examples/signature/basic.teal")
    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        assert compileTeal(program, Mode.Signature) == target

def test_atomic_swap():
    from examples.signature.atomic_swap import htlc

    program = htlc()

    target_path = os.path.join(os.path.dirname(__file__), "../examples/signature/atomic_swap.teal")
    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        assert compileTeal(program, Mode.Signature) == target

def test_periodic_payment():
    from examples.signature.periodic_payment import periodic_payment

    program = periodic_payment()

    target_path = os.path.join(os.path.dirname(__file__), "../examples/signature/periodic_payment.teal")
    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        assert compileTeal(program, Mode.Signature) == target

def test_split():
    from examples.signature.split import split

    program = split(
        tmpl_own = Addr("SXOUGKH6RM5SO5A2JAZ5LR3CRM2JWL4LPQDCNRQO2IMLIMEH6T4QWKOREE"),
        tmpl_ratn = Int(32),
        tmpl_ratd = Int(68),
        tmpl_min_pay = Int(5000000),
        tmpl_timeout = Int(30000)
    )

    target = """#pragma version 2
txn TypeEnum
int pay
==
txn Fee
int 1000
<
&&
txn RekeyTo
global ZeroAddress
==
&&
global GroupSize
int 2
==
bnz l0
txn CloseRemainderTo
addr SXOUGKH6RM5SO5A2JAZ5LR3CRM2JWL4LPQDCNRQO2IMLIMEH6T4QWKOREE
==
txn Receiver
global ZeroAddress
==
&&
txn Amount
int 0
==
&&
txn FirstValid
int 30000
>
&&
b l1
l0:
gtxn 0 Sender
gtxn 1 Sender
==
txn CloseRemainderTo
global ZeroAddress
==
&&
gtxn 0 Receiver
addr 6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY
==
&&
gtxn 1 Receiver
addr 7Z5PWO2C6LFNQFGHWKSK5H47IQP5OJW2M3HA2QPXTY3WTNP5NU2MHBW27M
==
&&
gtxn 0 Amount
gtxn 0 Amount
gtxn 1 Amount
+
int 32
*
int 68
/
==
&&
gtxn 0 Amount
int 5000000
==
&&
l1:
&&"""
    reset_label_count()
    assert compileTeal(program, Mode.Signature) == target

def test_dutch_auction():
    from examples.signature.dutch_auction import dutch_auction

    program = dutch_auction()

    target_path = os.path.join(os.path.dirname(__file__), "../examples/signature/dutch_auction.teal")
    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        reset_label_count()
        assert compileTeal(program, Mode.Signature) == target

def test_recurring_swap():
    from examples.signature.recurring_swap import recurring_swap

    program = recurring_swap()

    target_path = os.path.join(os.path.dirname(__file__), "../examples/signature/recurring_swap.teal")
    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        reset_label_count()
        assert compileTeal(program, Mode.Signature) == target

def test_asset():
    from examples.application.asset import approval_program, clear_state_program

    approval = approval_program()
    clear_state = clear_state_program()

    # only checking for successful compilation for now
    compileTeal(approval, Mode.Application)
    compileTeal(clear_state, Mode.Application)

def test_security_token():
    from examples.application.security_token import approval_program, clear_state_program

    approval = approval_program()
    clear_state = clear_state_program()
    
    # only checking for successful compilation for now
    compileTeal(approval, Mode.Application)
    compileTeal(clear_state, Mode.Application)

def test_vote():
    from examples.application.vote import approval_program, clear_state_program

    approval = approval_program()
    clear_state = clear_state_program()
    
    # only checking for successful compilation for now
    compileTeal(approval, Mode.Application)
    compileTeal(clear_state, Mode.Application)

def test_cond():
	cond1 = Txn.fee() < Int(2000)
	cond2 = Txn.amount() > Int(5000)
	cond3 = Txn.receiver() == Txn.sender()
	core = Cond([Global.group_size()==Int(2), cond1],
				[Global.group_size()==Int(3), cond2],
				[Global.group_size()==Int(4), cond3])
	compileTeal(core, Mode.Signature)
