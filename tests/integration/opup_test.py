from graviton.blackbox import DryRunExecutor  # DryRunEncoder,

from pyteal import (
    compileTeal,
    Approve,
    Int,
    Mode,
    OpUp,
    OpUpMode,
    Seq,
    Subroutine,
    TealType,
)
from utils.blackbox import Blackbox, algod_with_assertion, blackbox_pyteal


def test_example():
    # Example 1: Using blackbox_pyteal for a simple test of both an app and logic sig:

    @Blackbox(input_types=[])
    @Subroutine(TealType.uint64)
    def opie():
        opup = OpUp(OpUpMode.Explicit, Int(1))
        return Seq(opup.ensure_budget(Int(3000)), Approve())

    # create pyteal app and logic sig approvals:
    approval_app = blackbox_pyteal(opie, Mode.Application)

    # compile the evaluated approvals to generate TEAL:
    app_teal = compileTeal(approval_app(), Mode.Application, version=6)

    args = []

    # evaluate the programs
    algod = algod_with_assertion()
    app_result = DryRunExecutor.dryrun_app(algod, app_teal, args)

    assert app_result.cost() == 12
    # # check to see that x^2 is at the top of the stack as expected
    # assert app_result.stack_top() == x**2, app_result.report(
    #     args, "stack_top() gave unexpected results for app"
    # )
    # assert lsig_result.stack_top() == x**2, lsig_result.report(
    #     args, "stack_top() gave unexpected results for lsig"
    # )

    # # check to see that itob of x^2 has been logged (only for the app case)
    # assert app_result.last_log() == DryRunEncoder.hex(x**2), app_result.report(
    #     args, "last_log() gave unexpected results from app"
    # )
