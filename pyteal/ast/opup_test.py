import pytest

from pyteal.ast.opup import OpUp, OpUpMode

import pyteal as pt


def test_opup_explicit():
    mode = OpUpMode.Explicit
    with pytest.raises(pt.TealInputError) as err:
        opup = OpUp(mode)
    assert "target_app_id must be specified in Explicit OpUp mode" in str(err.value)

    with pytest.raises(pt.TealTypeError):
        opup = OpUp(mode, pt.Bytes("appid"))

    opup = OpUp(mode, pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        opup.ensure_budget(pt.Bytes("budget"))

    with pytest.raises(pt.TealTypeError):
        opup.maximize_budget(pt.Bytes("fee"))

    assert opup.target_app_id == pt.Int(1)

    # verify correct usage doesn't cause an error
    _ = pt.Seq(opup.ensure_budget(pt.Int(500) + pt.Int(1000)), pt.Return(pt.Int(1)))

    _ = pt.Seq(opup.maximize_budget(pt.Txn.fee() - pt.Int(100)), pt.Return(pt.Int(1)))


def test_opup_oncall():
    mode = OpUpMode.OnCall
    opup = OpUp(mode)

    with pytest.raises(pt.TealTypeError):
        opup.ensure_budget(pt.Bytes("budget"))

    with pytest.raises(pt.TealTypeError):
        opup.maximize_budget(pt.Bytes("fee"))

    # verify correct usage doesn't cause an error
    _ = pt.Seq(opup.ensure_budget(pt.Int(500) + pt.Int(1000)), pt.Return(pt.Int(1)))

    _ = pt.Seq(opup.maximize_budget(pt.Txn.fee() - pt.Int(100)), pt.Return(pt.Int(1)))
