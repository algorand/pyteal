import pytest

from pyteal.ast.opup import OpUp, OpUpMode

from .. import *


def test_opup_explicit():
    mode = OpUpMode.Explicit
    with pytest.raises(TealInputError) as err:
        opup = OpUp(mode)
    assert "target_app_id must be specified in Explicit OpUp mode" in str(err.value)

    with pytest.raises(TealTypeError):
        opup = OpUp(mode, Bytes("appid"))

    opup = OpUp(mode, Int(1))

    with pytest.raises(TealTypeError):
        opup.ensure_budget(Bytes("budget"))

    with pytest.raises(TealTypeError):
        opup.maximize_budget(Bytes("fee"))

    assert opup.target_app_id == Int(1)

    # verify correct usage doesn't cause an error
    program_with_ensure = Seq(opup.ensure_budget(Int(500) + Int(1000)), Return(Int(1)))

    program_with_maximize = Seq(
        opup.maximize_budget(Txn.fee() - Int(100)), Return(Int(1))
    )


def test_opup_oncall():
    mode = OpUpMode.OnCall
    opup = OpUp(mode)

    with pytest.raises(TealTypeError):
        opup.ensure_budget(Bytes("budget"))

    with pytest.raises(TealTypeError):
        opup.maximize_budget(Bytes("fee"))

    # verify correct usage doesn't cause an error
    program_with_ensure = Seq(opup.ensure_budget(Int(500) + Int(1000)), Return(Int(1)))

    assert opup.target_app_id is not None
    assert opup.target_app_id_slot is not None

    program_with_maximize = Seq(
        opup.maximize_budget(Txn.fee() - Int(100)), Return(Int(1))
    )
