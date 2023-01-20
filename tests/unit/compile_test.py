from pathlib import Path
import pytest
import json

import pyteal as pt


def test_abi_algobank():
    from examples.application.abi.algobank import (
        approval_program,
        clear_state_program,
        contract,
    )

    target_dir = Path.cwd() / "examples" / "application" / "abi"

    with open(
        target_dir / "algobank_approval.teal", "r"
    ) as expected_approval_program_file:
        expected_approval_program = "".join(
            expected_approval_program_file.readlines()
        ).strip()
        assert approval_program == expected_approval_program

    with open(
        target_dir / "algobank_clear_state.teal", "r"
    ) as expected_clear_state_program_file:
        expected_clear_state_program = "".join(
            expected_clear_state_program_file.readlines()
        ).strip()
        assert clear_state_program == expected_clear_state_program

    with open(target_dir / "algobank.json", "r") as expected_contract_file:
        expected_contract = json.load(expected_contract_file)
        assert contract.dictify() == expected_contract


def test_basic_bank():
    from examples.signature.basic import bank_for_account

    program = bank_for_account(
        "ZZAF5ARA4MEC5PVDOP64JM5O5MQST63Q2KOY2FLYFLXXD3PFSNJJBYAFZM"
    )

    target_path = Path.cwd() / "examples" / "signature" / "basic.teal"

    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        assert pt.compileTeal(program, mode=pt.Mode.Signature, version=3) == target


def test_atomic_swap():
    from examples.signature.atomic_swap import htlc

    program = htlc()

    target_path = Path.cwd() / "examples" / "signature" / "atomic_swap.teal"

    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        assert pt.compileTeal(program, mode=pt.Mode.Signature, version=2) == target


def test_periodic_payment():
    from examples.signature.periodic_payment import periodic_payment

    program = periodic_payment()

    target_path = Path.cwd() / "examples" / "signature" / "periodic_payment.teal"
    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        assert pt.compileTeal(program, mode=pt.Mode.Signature, version=2) == target


def test_split():
    from examples.signature.split import split

    program = split()

    target_path = Path.cwd() / "examples" / "signature" / "split.teal"

    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        assert pt.compileTeal(program, mode=pt.Mode.Signature, version=2) == target


def test_dutch_auction():
    from examples.signature.dutch_auction import dutch_auction

    program = dutch_auction()

    target_path = Path.cwd() / "examples" / "signature" / "dutch_auction.teal"

    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        assert pt.compileTeal(program, mode=pt.Mode.Signature, version=2) == target


def test_recurring_swap():
    from examples.signature.recurring_swap import recurring_swap

    program = recurring_swap()

    target_path = Path.cwd() / "examples" / "signature" / "recurring_swap.teal"

    with open(target_path, "r") as target_file:
        target = "".join(target_file.readlines()).strip()
        assert pt.compileTeal(program, mode=pt.Mode.Signature, version=2) == target


def test_asset():
    from examples.application.asset import approval_program, clear_state_program

    approval = approval_program()
    clear_state = clear_state_program()

    # only checking for successful compilation for now
    pt.compileTeal(approval, mode=pt.Mode.Application, version=2)
    pt.compileTeal(clear_state, mode=pt.Mode.Application, version=2)


def test_security_token():
    from examples.application.security_token import (
        approval_program,
        clear_state_program,
    )

    approval = approval_program()
    clear_state = clear_state_program()

    # only checking for successful compilation for now
    pt.compileTeal(approval, mode=pt.Mode.Application, version=2)
    pt.compileTeal(clear_state, mode=pt.Mode.Application, version=2)


def test_vote():
    from examples.application.vote import approval_program, clear_state_program

    approval = approval_program()
    clear_state = clear_state_program()

    # only checking for successful compilation for now
    pt.compileTeal(approval, mode=pt.Mode.Application, version=2)
    pt.compileTeal(clear_state, mode=pt.Mode.Application, version=2)


def test_cond():
    cond1 = pt.Txn.fee() < pt.Int(2000)
    cond2 = pt.Txn.amount() > pt.Int(5000)
    cond3 = pt.Txn.receiver() == pt.Txn.sender()
    core = pt.Cond(
        [pt.Global.group_size() == pt.Int(2), cond1],
        [pt.Global.group_size() == pt.Int(3), cond2],
        [pt.Global.group_size() == pt.Int(4), cond3],
    )
    pt.compileTeal(core, mode=pt.Mode.Signature, version=2)


@pytest.mark.timeout(2)
def test_many_ifs():
    """
    Test with many pt.If statements to trigger potential corner cases in code generation.
    Previous versions of PyTeal took an exponential time to generate the TEAL code for this PyTEAL.
    """

    sv = pt.ScratchVar(pt.TealType.uint64)
    s = pt.Seq(
        [
            pt.If(
                pt.Int(3 * i) == pt.Int(3 * i),
                sv.store(pt.Int(3 * i + 1)),
                sv.store(pt.Int(3 * i + 2)),
            )
            for i in range(30)
        ]
        + [pt.Return(sv.load())]
    )

    pt.compileTeal(s, mode=pt.Mode.Signature, version=2)
