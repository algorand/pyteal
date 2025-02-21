import pytest

import pyteal as pt

avm1Options = pt.CompileOptions(version=10)
avm11Options = pt.CompileOptions(version=11)


def test_online_stake_teal_10():
    with pytest.raises(pt.TealInputError):
        pt.OnlineStake().__teal__(avm1Options)


def test_online_stake():
    expr = pt.OnlineStake()
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock([pt.TealOp(expr, pt.Op.online_stake)])

    actual, _ = expr.__teal__(avm11Options)

    assert actual == expected
