import pytest
from typing import Union, List, cast

import pyteal as pt

avm4Options = pt.CompileOptions(version=4)
avm5Options = pt.CompileOptions(version=5)
avm7Options = pt.CompileOptions(version=7)

curve_options_map = {
    pt.EcdsaCurve.Secp256k1: avm5Options,
    pt.EcdsaCurve.Secp256r1: avm7Options,
}


@pytest.mark.parametrize("curve", [pt.EcdsaCurve.Secp256k1, pt.EcdsaCurve.Secp256r1])
def test_ecdsa_decompress(curve: pt.EcdsaCurve):
    compressed_pubkey = pt.Bytes("XY")
    pubkey = pt.EcdsaDecompress(curve, compressed_pubkey)
    assert pubkey.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(compressed_pubkey, pt.Op.byte, '"XY"'),
            pt.TealOp(pubkey, pt.Op.ecdsa_pk_decompress, curve.arg_name),
            pt.TealOp(
                pubkey.output_slots[1].store(), pt.Op.store, pubkey.output_slots[1]
            ),
            pt.TealOp(
                pubkey.output_slots[0].store(), pt.Op.store, pubkey.output_slots[0]
            ),
        ]
    )

    actual, _ = pubkey.__teal__(curve_options_map[curve])
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    # compile without errors this is necessary so assembly is also tested
    pt.compileTeal(
        pt.Seq(pubkey, pt.Approve()), pt.Mode.Application, version=curve.min_version
    )

    with pytest.raises(pt.TealInputError):
        pt.compileTeal(
            pt.Seq(pubkey, pt.Approve()),
            pt.Mode.Application,
            version=curve.min_version - 1,
        )


@pytest.mark.parametrize("curve", [pt.EcdsaCurve.Secp256k1, pt.EcdsaCurve.Secp256r1])
def test_ecdsa_recover(curve: pt.EcdsaCurve):
    if curve != pt.EcdsaCurve.Secp256k1:
        with pytest.raises(pt.TealInputError):
            pt.EcdsaRecover(
                curve, pt.Bytes("data"), pt.Int(1), pt.Bytes("sigA"), pt.Bytes("sigB")
            )
    else:
        args = [pt.Bytes("data"), pt.Int(1), pt.Bytes("sigA"), pt.Bytes("sigB")]
        pubkey = pt.EcdsaRecover(curve, args[0], args[1], args[2], args[3])
        assert pubkey.type_of() == pt.TealType.none

        expected = pt.TealSimpleBlock(
            [
                pt.TealOp(args[0], pt.Op.byte, '"data"'),
                pt.TealOp(args[1], pt.Op.int, 1),
                pt.TealOp(args[2], pt.Op.byte, '"sigA"'),
                pt.TealOp(args[3], pt.Op.byte, '"sigB"'),
                pt.TealOp(pubkey, pt.Op.ecdsa_pk_recover, curve.arg_name),
                pt.TealOp(
                    pubkey.output_slots[1].store(), pt.Op.store, pubkey.output_slots[1]
                ),
                pt.TealOp(
                    pubkey.output_slots[0].store(), pt.Op.store, pubkey.output_slots[0]
                ),
            ]
        )

        actual, _ = pubkey.__teal__(curve_options_map[curve])
        actual.addIncoming()
        actual = pt.TealBlock.NormalizeBlocks(actual)

        with pt.TealComponent.Context.ignoreExprEquality():
            assert actual == expected

        # compile without errors this is necessary so assembly is also tested
        pt.compileTeal(
            pt.Seq(pubkey, pt.Approve()), pt.Mode.Application, version=curve.min_version
        )

        with pytest.raises(pt.TealInputError):
            pt.compileTeal(
                pt.Seq(pubkey, pt.Approve()),
                pt.Mode.Application,
                version=curve.min_version - 1,
            )


@pytest.mark.parametrize("curve", [pt.EcdsaCurve.Secp256k1, pt.EcdsaCurve.Secp256r1])
def test_ecdsa_verify_basic(curve: pt.EcdsaCurve):
    args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
    pubkey = (pt.Bytes("X"), pt.Bytes("Y"))
    expr = pt.EcdsaVerify(curve, args[0], args[1], args[2], pubkey)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"data"'),
            pt.TealOp(args[1], pt.Op.byte, '"sigA"'),
            pt.TealOp(args[2], pt.Op.byte, '"sigB"'),
            pt.TealOp(pubkey[0], pt.Op.byte, '"X"'),
            pt.TealOp(pubkey[1], pt.Op.byte, '"Y"'),
            pt.TealOp(expr, pt.Op.ecdsa_verify, curve.arg_name),
        ]
    )

    actual, _ = expr.__teal__(curve_options_map[curve])
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    # compile without errors this is necessary so assembly is also tested
    pt.compileTeal(
        pt.Seq(pt.Pop(expr), pt.Approve()),
        pt.Mode.Application,
        version=curve.min_version,
    )

    with pytest.raises(pt.TealInputError):
        pt.compileTeal(
            pt.Seq(pt.Pop(expr), pt.Approve()),
            pt.Mode.Application,
            version=curve.min_version - 1,
        )


@pytest.mark.parametrize("curve", [pt.EcdsaCurve.Secp256k1, pt.EcdsaCurve.Secp256r1])
def test_ecdsa_verify_compressed_pk(curve: pt.EcdsaCurve):
    args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
    compressed_pubkey = pt.Bytes("XY")
    pubkey = pt.EcdsaDecompress(curve, compressed_pubkey)
    expr = pt.EcdsaVerify(curve, args[0], args[1], args[2], pubkey)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(compressed_pubkey, pt.Op.byte, '"XY"'),
            pt.TealOp(pubkey, pt.Op.ecdsa_pk_decompress, curve.arg_name),
            pt.TealOp(
                pubkey.output_slots[1].store(), pt.Op.store, pubkey.output_slots[1]
            ),
            pt.TealOp(
                pubkey.output_slots[0].store(), pt.Op.store, pubkey.output_slots[0]
            ),
            pt.TealOp(args[0], pt.Op.byte, '"data"'),
            pt.TealOp(args[1], pt.Op.byte, '"sigA"'),
            pt.TealOp(args[2], pt.Op.byte, '"sigB"'),
            pt.TealOp(
                pubkey.output_slots[0].load(), pt.Op.load, pubkey.output_slots[0]
            ),
            pt.TealOp(
                pubkey.output_slots[1].load(), pt.Op.load, pubkey.output_slots[1]
            ),
            pt.TealOp(expr, pt.Op.ecdsa_verify, curve.arg_name),
        ]
    )

    actual, _ = expr.__teal__(curve_options_map[curve])
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    # compile without errors this is necessary so assembly is also tested
    pt.compileTeal(
        pt.Seq(pt.Pop(expr), pt.Approve()),
        pt.Mode.Application,
        version=curve.min_version,
    )

    with pytest.raises(pt.TealInputError):
        pt.compileTeal(
            pt.Seq(pt.Pop(expr), pt.Approve()),
            pt.Mode.Application,
            version=curve.min_version - 1,
        )


def test_ecdsa_verify_recovered_pk():
    curve = pt.EcdsaCurve.Secp256k1
    args = [pt.Bytes("data"), pt.Int(1), pt.Bytes("sigA"), pt.Bytes("sigB")]
    pubkey = pt.EcdsaRecover(curve, args[0], args[1], args[2], args[3])
    expr = pt.EcdsaVerify(curve, args[0], args[2], args[3], pubkey)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"data"'),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(args[2], pt.Op.byte, '"sigA"'),
            pt.TealOp(args[3], pt.Op.byte, '"sigB"'),
            pt.TealOp(pubkey, pt.Op.ecdsa_pk_recover, curve.arg_name),
            pt.TealOp(
                pubkey.output_slots[1].store(), pt.Op.store, pubkey.output_slots[1]
            ),
            pt.TealOp(
                pubkey.output_slots[0].store(), pt.Op.store, pubkey.output_slots[0]
            ),
            pt.TealOp(args[0], pt.Op.byte, '"data"'),
            pt.TealOp(args[1], pt.Op.byte, '"sigA"'),
            pt.TealOp(args[2], pt.Op.byte, '"sigB"'),
            pt.TealOp(
                pubkey.output_slots[0].load(), pt.Op.load, pubkey.output_slots[0]
            ),
            pt.TealOp(
                pubkey.output_slots[1].load(), pt.Op.load, pubkey.output_slots[1]
            ),
            pt.TealOp(expr, pt.Op.ecdsa_verify, curve.arg_name),
        ]
    )

    actual, _ = expr.__teal__(curve_options_map[curve])
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    # compile without errors this is necessary so assembly is also tested
    pt.compileTeal(
        pt.Seq(pt.Pop(expr), pt.Approve()),
        pt.Mode.Application,
        version=curve.min_version,
    )

    with pytest.raises(pt.TealInputError):
        pt.compileTeal(
            pt.Seq(pt.Pop(expr), pt.Approve()),
            pt.Mode.Application,
            version=curve.min_version - 1,
        )


@pytest.mark.parametrize("curve", [pt.EcdsaCurve.Secp256k1, pt.EcdsaCurve.Secp256r1])
def test_ecdsa_invalid(curve: pt.EcdsaCurve):
    if curve == pt.EcdsaCurve.Secp256k1:
        with pytest.raises(pt.TealTypeError):
            args: List[Union[pt.Bytes, pt.Int]] = [
                pt.Bytes("data"),
                pt.Bytes("1"),
                pt.Bytes("sigA"),
                pt.Bytes("sigB"),
            ]
            pt.EcdsaRecover(curve, args[0], args[1], args[2], args[3])

    with pytest.raises(pt.TealTypeError):
        pt.EcdsaDecompress(curve, pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
        pubkey: Union[tuple[pt.Bytes, Union[pt.Int, pt.Bytes]], pt.MultiValue] = (
            pt.Bytes("X"),
            pt.Int(1),
        )
        pt.EcdsaVerify(curve, args[0], args[1], args[2], pubkey)

    with pytest.raises(pt.TealTypeError):
        args = [pt.Bytes("data"), pt.Int(1), pt.Bytes("sigB")]
        pubkey = (pt.Bytes("X"), pt.Bytes("Y"))
        pt.EcdsaVerify(curve, args[0], args[1], args[2], pubkey)

    with pytest.raises(pt.TealTypeError):
        args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
        compressed_pk = pt.Bytes("XY")
        pubkey = pt.MultiValue(
            pt.Op.ecdsa_pk_decompress,
            [pt.TealType.uint64, pt.TealType.bytes],
            immediate_args=[curve.__str__()],
            args=[compressed_pk],
        )
        pt.EcdsaVerify(curve, args[0], args[1], args[2], pubkey)

    with pytest.raises(pt.TealInputError):
        args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
        pubkey = (pt.Bytes("X"), pt.Bytes("Y"))
        expr = pt.EcdsaVerify(curve, args[0], args[1], args[2], pubkey)

        expr.__teal__(avm4Options)

    with pytest.raises(pt.TealTypeError):
        args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
        pubkey = (pt.Bytes("X"), pt.Bytes("Y"))
        expr = pt.EcdsaVerify(cast(pt.EcdsaCurve, 5), args[0], args[1], args[2], pubkey)
