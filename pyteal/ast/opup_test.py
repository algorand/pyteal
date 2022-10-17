import pytest

from pyteal.ast.opup import OpUp, OpUpFeePayer, OpUpMode

import pyteal as pt


def test_opup_explicit():
    mode = OpUpMode.Explicit
    with pytest.raises(pt.TealInputError) as err:
        opup = OpUp(mode)
    assert "target_app_id must be specified in Explicit OpUp mode" in str(err.value)

    with pytest.raises(pt.TealTypeError):
        opup = OpUp(mode, target_app_id=pt.Bytes("appid"))

    opup = OpUp(mode, target_app_id=pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        opup.ensure_budget(required_budget=pt.Bytes("budget"))

    with pytest.raises(pt.TealTypeError):
        opup.ensure_budget(required_budget=pt.Int(1_000), inner_fee=pt.Bytes("min_fee"))

    with pytest.raises(pt.TealTypeError):
        opup.maximize_budget(fee=pt.Bytes("fee"))

    with pytest.raises(pt.TealTypeError):
        opup.maximize_budget(fee=pt.Int(1_000), payer=pt.Bytes("payer"))

    assert opup.target_app_id == pt.Int(1)

    # verify correct usage doesn't cause an error
    opup = OpUp(mode, target_app_id=pt.Int(1))
    _ = pt.Seq(
        opup.ensure_budget(required_budget=pt.Int(500) + pt.Int(1000)),
        pt.Return(pt.Int(1)),
    )
    _ = pt.Seq(
        opup.ensure_budget(
            required_budget=pt.Int(500) + pt.Int(1000),
            inner_fee=pt.Global.min_txn_fee(),
        ),
        pt.Return(pt.Int(1)),
    )

    opup = OpUp(mode, target_app_id=pt.Int(1))
    _ = pt.Seq(
        opup.maximize_budget(fee=pt.Txn.fee() - pt.Int(100)), pt.Return(pt.Int(1))
    )
    _ = pt.Seq(
        opup.maximize_budget(fee=pt.Txn.fee() - pt.Int(100), payer=OpUpFeePayer.Any),
        pt.Return(pt.Int(1)),
    )


def test_opup_oncall():
    mode = OpUpMode.OnCall
    opup = OpUp(mode)

    with pytest.raises(pt.TealTypeError):
        opup.ensure_budget(required_budget=pt.Bytes("budget"))

    with pytest.raises(pt.TealTypeError):
        opup.ensure_budget(required_budget=pt.Int(1_000), inner_fee=pt.Bytes("min_fee"))

    with pytest.raises(pt.TealTypeError):
        opup.maximize_budget(fee=pt.Bytes("fee"))

    with pytest.raises(pt.TealTypeError):
        opup.maximize_budget(fee=pt.Int(1_000), payer=pt.Bytes("min_fee"))

    # verify correct usage doesn't cause an error
    opup = OpUp(mode)
    _ = pt.Seq(
        opup.ensure_budget(required_budget=pt.Int(500) + pt.Int(1000)),
        pt.Return(pt.Int(1)),
    )
    _ = pt.Seq(
        opup.ensure_budget(
            required_budget=pt.Int(500) + pt.Int(1000),
            inner_fee=pt.Global.min_txn_fee(),
        ),
        pt.Return(pt.Int(1)),
    )

    opup = OpUp(mode)
    _ = pt.Seq(
        opup.maximize_budget(fee=pt.Txn.fee() - pt.Int(100)), pt.Return(pt.Int(1))
    )
    _ = pt.Seq(
        opup.maximize_budget(fee=pt.Txn.fee() - pt.Int(100), payer=OpUpFeePayer.Any),
        pt.Return(pt.Int(1)),
    )
