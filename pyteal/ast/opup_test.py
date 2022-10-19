import pytest
from typing import NamedTuple

import pyteal as pt

avm6Options = pt.CompileOptions(version=6)


def test_OpUp_init():
    app_id = pt.Int(1)
    opup_explicit = pt.OpUp(pt.OpUpMode.Explicit, target_app_id=app_id)
    assert opup_explicit.mode is pt.OpUpMode.Explicit
    assert opup_explicit.target_app_id is app_id

    with pytest.raises(
        pt.TealInputError, match="target_app_id must be specified in Explicit OpUp mode"
    ):
        pt.OpUp(pt.OpUpMode.Explicit)

    with pytest.raises(pt.TealTypeError):
        pt.OpUp(pt.OpUpMode.Explicit, target_app_id=pt.Bytes("appid"))

    opup_oncall = pt.OpUp(pt.OpUpMode.OnCall)
    assert opup_oncall.mode is pt.OpUpMode.OnCall
    assert opup_oncall.target_app_id is None

    with pytest.raises(
        pt.TealInputError, match="target_app_id is not used in OnCall OpUp mode"
    ):
        pt.OpUp(pt.OpUpMode.OnCall, target_app_id=app_id)

    with pytest.raises(pt.TealInputError, match="Invalid OpUp mode provided"):
        pt.OpUp(None)


class OpUpTest(NamedTuple):
    opup: pt.OpUp
    fee_source: pt.OpUpFeeSource | None
    expected_inner_fields: dict[pt.TxnField, pt.Expr | list[pt.Expr]]


OP_UP_TEST_CASES: list[OpUpTest] = [
    OpUpTest(
        opup=pt.OpUp(pt.OpUpMode.Explicit, target_app_id=pt.Int(9)),
        fee_source=None,
        expected_inner_fields={
            pt.TxnField.type_enum: pt.TxnType.ApplicationCall,
            pt.TxnField.application_id: pt.Int(9),
        },
    ),
    OpUpTest(
        opup=pt.OpUp(pt.OpUpMode.Explicit, target_app_id=pt.Int(876)),
        fee_source=pt.OpUpFeeSource.Any,
        expected_inner_fields={
            pt.TxnField.type_enum: pt.TxnType.ApplicationCall,
            pt.TxnField.application_id: pt.Int(876),
        },
    ),
    OpUpTest(
        opup=pt.OpUp(pt.OpUpMode.Explicit, target_app_id=pt.Int(1000001)),
        fee_source=pt.OpUpFeeSource.GroupCredit,
        expected_inner_fields={
            pt.TxnField.type_enum: pt.TxnType.ApplicationCall,
            pt.TxnField.fee: pt.Int(0),
            pt.TxnField.application_id: pt.Int(1000001),
        },
    ),
    OpUpTest(
        opup=pt.OpUp(pt.OpUpMode.Explicit, target_app_id=pt.Int(3)),
        fee_source=pt.OpUpFeeSource.AppAccount,
        expected_inner_fields={
            pt.TxnField.type_enum: pt.TxnType.ApplicationCall,
            pt.TxnField.fee: pt.Global.min_txn_fee(),
            pt.TxnField.application_id: pt.Int(3),
        },
    ),
    OpUpTest(
        opup=pt.OpUp(pt.OpUpMode.OnCall),
        fee_source=None,
        expected_inner_fields={
            pt.TxnField.type_enum: pt.TxnType.ApplicationCall,
            pt.TxnField.on_completion: pt.OnComplete.DeleteApplication,
            pt.TxnField.approval_program: pt.Bytes("base16", "068101"),
            pt.TxnField.clear_state_program: pt.Bytes("base16", "068101"),
        },
    ),
    OpUpTest(
        opup=pt.OpUp(pt.OpUpMode.OnCall),
        fee_source=pt.OpUpFeeSource.Any,
        expected_inner_fields={
            pt.TxnField.type_enum: pt.TxnType.ApplicationCall,
            pt.TxnField.on_completion: pt.OnComplete.DeleteApplication,
            pt.TxnField.approval_program: pt.Bytes("base16", "068101"),
            pt.TxnField.clear_state_program: pt.Bytes("base16", "068101"),
        },
    ),
    OpUpTest(
        opup=pt.OpUp(pt.OpUpMode.OnCall),
        fee_source=pt.OpUpFeeSource.GroupCredit,
        expected_inner_fields={
            pt.TxnField.type_enum: pt.TxnType.ApplicationCall,
            pt.TxnField.fee: pt.Int(0),
            pt.TxnField.on_completion: pt.OnComplete.DeleteApplication,
            pt.TxnField.approval_program: pt.Bytes("base16", "068101"),
            pt.TxnField.clear_state_program: pt.Bytes("base16", "068101"),
        },
    ),
    OpUpTest(
        opup=pt.OpUp(pt.OpUpMode.OnCall),
        fee_source=pt.OpUpFeeSource.AppAccount,
        expected_inner_fields={
            pt.TxnField.type_enum: pt.TxnType.ApplicationCall,
            pt.TxnField.fee: pt.Global.min_txn_fee(),
            pt.TxnField.on_completion: pt.OnComplete.DeleteApplication,
            pt.TxnField.approval_program: pt.Bytes("base16", "068101"),
            pt.TxnField.clear_state_program: pt.Bytes("base16", "068101"),
        },
    ),
]


def test_OP_UP_TEST_CASES_is_exhaustive():
    fee_sources: list[pt.OpUpFeeSource | None] = [fs for fs in pt.OpUpFeeSource]
    fee_sources.append(None)

    for mode, fee_source in zip(pt.OpUpMode, fee_sources):
        found_combination = False

        for test_case in OP_UP_TEST_CASES:
            if test_case.opup.mode is mode and test_case.fee_source is fee_source:
                found_combination = True
                break

        assert (
            found_combination
        ), f"Combination not found in test cases: mode={mode}, fee_source={fee_source}"


@pytest.mark.parametrize("opup, fee_source, expected_inner_fields", OP_UP_TEST_CASES)
def test_OpUp_ensure_budget(
    opup: pt.OpUp,
    fee_source: pt.OpUpFeeSource | None,
    expected_inner_fields: dict[pt.TxnField, pt.Expr | list[pt.Expr]],
):
    required_budget = pt.Int(777)
    expr = (
        opup.ensure_budget(required_budget)
        if fee_source is None
        else opup.ensure_budget(required_budget, fee_source)
    )
    assert expr.type_of() == pt.TealType.none
    assert expr.has_return() is False

    intermediate_value = pt.ScratchVar()
    expected_expr = pt.Seq(
        intermediate_value.store(required_budget + pt.Int(10)),
        pt.While(intermediate_value.load() > pt.Global.opcode_budget()).Do(
            pt.InnerTxnBuilder.Execute(expected_inner_fields)
        ),
    )
    expected, _ = expected_expr.__teal__(avm6Options)
    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(avm6Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreScratchSlotEquality(), pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    assert pt.TealBlock.MatchScratchSlotReferences(
        pt.TealBlock.GetReferencedScratchSlots(actual),
        pt.TealBlock.GetReferencedScratchSlots(expected),
    )

    with pytest.raises(pt.TealTypeError):
        opup.ensure_budget(required_budget=pt.Bytes("budget"))

    with pytest.raises(pt.TealTypeError):
        opup.ensure_budget(
            required_budget=required_budget, fee_source=pt.Bytes("fee_src")  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("opup, fee_source, expected_inner_fields", OP_UP_TEST_CASES)
def test_OpUp_maximize_budget(
    opup: pt.OpUp,
    fee_source: pt.OpUpFeeSource | None,
    expected_inner_fields: dict[pt.TxnField, pt.Expr | list[pt.Expr]],
):
    fee = pt.Int(12345)
    expr = (
        opup.maximize_budget(fee)
        if fee_source is None
        else opup.maximize_budget(fee, fee_source)
    )
    assert expr.type_of() == pt.TealType.none
    assert expr.has_return() is False

    intermediate_value = pt.ScratchVar()
    expected_expr = pt.For(
        intermediate_value.store(pt.Int(0)),
        intermediate_value.load() < fee / pt.Global.min_txn_fee(),
        intermediate_value.store(intermediate_value.load() + pt.Int(1)),
    ).Do(pt.InnerTxnBuilder.Execute(expected_inner_fields))
    expected, _ = expected_expr.__teal__(avm6Options)
    expected.addIncoming()
    expected = pt.TealBlock.NormalizeBlocks(expected)

    actual, _ = expr.__teal__(avm6Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreScratchSlotEquality(), pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    assert pt.TealBlock.MatchScratchSlotReferences(
        pt.TealBlock.GetReferencedScratchSlots(actual),
        pt.TealBlock.GetReferencedScratchSlots(expected),
    )

    with pytest.raises(pt.TealTypeError):
        opup.maximize_budget(fee=pt.Bytes("fee"))

    with pytest.raises(pt.TealTypeError):
        opup.maximize_budget(fee=fee, fee_source=pt.Bytes("fee_src"))  # type: ignore[arg-type]
