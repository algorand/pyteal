import pytest

import pyteal as pt

avm10Options = pt.CompileOptions(version=10)
avm11Options = pt.CompileOptions(version=11)


def test_mimc_bn254():
    args = [pt.Bytes("a message in a bottle")]
    expr = pt.MiMC.bn254mp110(*args)
    assert expr.type_of() == pt.TealType.bytes

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"a message in a bottle"'),
            pt.TealOp(expr, pt.Op.mimc, "BN254Mp110"),
        ]
    )

    actual, _ = expr.__teal__(avm11Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    with pytest.raises(pt.TealInputError):
        expr.__teal__(avm10Options)


def test_json_ref_invalid():
    with pytest.raises(pt.TealTypeError):
        pt.MiMC.bn254mp110(pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        pt.MiMC.bls12_381mp111(pt.Int(2))
