import graviton.models
import pytest
import math

from typing import cast
import pyteal as pt
from tests.blackbox import (
    Blackbox,
    BlackboxWrapper,
    PyTealDryRunExecutor,
)
from graviton.blackbox import (
    DryRunExecutor,
    DryRunInspector,
    DryRunTransactionParams as TxParams,
)

from algosdk.v2client.models import Account
import algosdk


def _dryrun(
    bw: BlackboxWrapper,
    sp: algosdk.transaction.SuggestedParams,
    accounts: list[Account | str],
) -> DryRunInspector:
    return PyTealDryRunExecutor(bw, pt.Mode.Application).dryrun_one(
        [],
        compiler_version=pt.compiler.MAX_PROGRAM_VERSION,
        txn_params=TxParams.for_app(
            sender=graviton.models.ZERO_ADDRESS,
            sp=sp,
            index=DryRunExecutor.EXISTING_APP_CALL,
            on_complete=algosdk.transaction.OnComplete.NoOpOC,
            dryrun_accounts=accounts,
        ),
    )


_application_opcode_budget = 700


@pytest.mark.parametrize("source", pt.OpUpFeeSource)
@pytest.mark.parametrize("inner_txn_count", range(1, 5))
@pytest.mark.parametrize("with_funding", [True, False])
@pytest.mark.serial  # Serial due to reused account + application state
def test_opup_maximize_budget(
    source: pt.OpUpFeeSource, inner_txn_count: int, with_funding: bool
):
    innerTxnFeeMicroAlgos = inner_txn_count * algosdk.constants.min_txn_fee

    @Blackbox(input_types=[])
    @pt.Subroutine(pt.TealType.uint64)
    def maximize_budget():
        return pt.Seq(
            pt.OpUp(mode=pt.OpUpMode.OnCall).maximize_budget(
                pt.Int(innerTxnFeeMicroAlgos), source
            ),
            pt.Global.opcode_budget(),
        )

    if with_funding:
        accounts: list[Account | str] = (
            [
                Account(
                    address=algosdk.logic.get_application_address(
                        DryRunExecutor.EXISTING_APP_CALL
                    ),
                    status="Offline",
                    amount=innerTxnFeeMicroAlgos,
                    amount_without_pending_rewards=innerTxnFeeMicroAlgos,
                )
            ]
            if source == pt.OpUpFeeSource.AppAccount
            else []
        )

        sp = DryRunExecutor.SUGGESTED_PARAMS
        sp.fee = (
            innerTxnFeeMicroAlgos + algosdk.constants.min_txn_fee
            if source == pt.OpUpFeeSource.GroupCredit
            else sp.fee
        )

        result = _dryrun(maximize_budget, sp, accounts)

        assert result.passed()
        assert result.budget_added() == _application_opcode_budget * inner_txn_count
    else:
        # Withholding account and/or transaction fee funding fails the
        # transaction.
        sp = DryRunExecutor.SUGGESTED_PARAMS
        sp.flat_fee = True
        sp.fee = algosdk.constants.min_txn_fee
        result = _dryrun(maximize_budget, DryRunExecutor.SUGGESTED_PARAMS, [])
        assert not result.passed()


@pytest.mark.parametrize("source", [f for f in pt.OpUpFeeSource])
@pytest.mark.parametrize("budget_added", range(1_000, 20_000, 2_500))
@pytest.mark.parametrize("with_funding", [True, False])
@pytest.mark.serial  # Serial due to reused account + application state
def test_opup_ensure_budget(
    source: pt.OpUpFeeSource, budget_added: int, with_funding: bool
):
    inner_txn_count = math.ceil(budget_added / _application_opcode_budget)
    innerTxnFeeMicroAlgos = (
        inner_txn_count * algosdk.constants.min_txn_fee + algosdk.constants.min_txn_fee
    )
    dryrun_starting_budget = 70_000  # https://github.com/algorand/go-algorand/blob/3a5e5847bebc21bfcae1f5fe056a78067b16c781/daemon/algod/api/server/v2/dryrun.go#L408

    @Blackbox(input_types=[])
    @pt.Subroutine(pt.TealType.uint64)
    def ensure_budget():
        return pt.Seq(
            pt.OpUp(mode=pt.OpUpMode.OnCall).ensure_budget(
                pt.Int(dryrun_starting_budget + budget_added), source
            ),
            pt.Global.opcode_budget(),
        )

    if with_funding:
        accounts: list[Account | str] = (
            [
                Account(
                    address=algosdk.logic.get_application_address(
                        DryRunExecutor.EXISTING_APP_CALL
                    ),
                    status="Offline",
                    amount=innerTxnFeeMicroAlgos,
                    amount_without_pending_rewards=innerTxnFeeMicroAlgos,
                )
            ]
            if source == pt.OpUpFeeSource.AppAccount
            else []
        )

        sp = DryRunExecutor.SUGGESTED_PARAMS
        sp.fee = (
            innerTxnFeeMicroAlgos + algosdk.constants.min_txn_fee
            if source == pt.OpUpFeeSource.GroupCredit
            else sp.fee
        )

        result = _dryrun(ensure_budget, sp, accounts)

        assert result.passed(), result.report()
        # Since ensure_budget guarantees _at least_ the required budget, the
        # assertions confirm minimum expected budget added without significantly
        # overshooting the mark.
        actual = cast(int, result.budget_added())
        threshold = _application_opcode_budget * inner_txn_count
        assert threshold <= actual <= threshold + _application_opcode_budget
    else:
        # Withholding account and/or transaction fee funding fails the
        # transaction.
        sp = DryRunExecutor.SUGGESTED_PARAMS
        sp.flat_fee = True
        sp.fee = algosdk.constants.min_txn_fee
        result = _dryrun(ensure_budget, DryRunExecutor.SUGGESTED_PARAMS, [])
        assert not result.passed()
