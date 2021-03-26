import os
from pyteal import *

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

    program = split()

    target_path = os.path.join(os.path.dirname(__file__), "../examples/signature/split.teal")
    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        assert compileTeal(program, Mode.Signature) == target

def test_dutch_auction():
    from examples.signature.dutch_auction import dutch_auction

    program = dutch_auction()

    target_path = os.path.join(os.path.dirname(__file__), "../examples/signature/dutch_auction.teal")
    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        assert compileTeal(program, Mode.Signature) == target

def test_recurring_swap():
    from examples.signature.recurring_swap import recurring_swap

    program = recurring_swap()

    target_path = os.path.join(os.path.dirname(__file__), "../examples/signature/recurring_swap.teal")
    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
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
