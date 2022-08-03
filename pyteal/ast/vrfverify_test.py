import pytest

import pyteal as pt

teal6Options = pt.CompileOptions(version=6)
teal7Options = pt.CompileOptions(version=7)


def test_vrf_verify_algorand():
    args = [pt.Bytes("a"), pt.Bytes("b"), pt.Bytes("c")]
    expr = pt.VrfVerify.algorand(*args)
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"a"'),
            pt.TealOp(args[1], pt.Op.byte, '"b"'),
            pt.TealOp(args[2], pt.Op.byte, '"c"'),
            pt.TealOp(expr, pt.Op.vrf_verify, "VrfAlgorand"),
            pt.TealOp(expr.output_slots[1], pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0], pt.Op.store, expr.output_slots[0]),
        ]
    )

    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(teal6Options)


def test_vrf_verify_chainlink():
    args = [pt.Bytes("a"), pt.Bytes("b"), pt.Bytes("c")]
    expr = pt.VrfVerify.chainlink(*args)
    assert expr.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"a"'),
            pt.TealOp(args[1], pt.Op.byte, '"b"'),
            pt.TealOp(args[2], pt.Op.byte, '"c"'),
            pt.TealOp(expr, pt.Op.vrf_verify, "VrfChainlink"),
            pt.TealOp(expr.output_slots[1], pt.Op.store, expr.output_slots[1]),
            pt.TealOp(expr.output_slots[0], pt.Op.store, expr.output_slots[0]),
        ]
    )

    actual, _ = expr.__teal__(teal7Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(teal6Options)


def test_vrf_verify_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.VrfVerify.algorand(pt.Int(0), pt.Bytes("b"), pt.Bytes("c"))

    with pytest.raises(pt.TealTypeError):
        pt.VrfVerify.chainlink(pt.Bytes("a"), pt.Int(0), pt.Bytes("c"))

    with pytest.raises(pt.TealTypeError):
        pt.VrfVerify.chainlink(pt.Bytes("a"), pt.Bytes("b"), pt.Int(0))
