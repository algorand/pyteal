import pytest

import pyteal as pt

teal4Options = pt.CompileOptions(version=4)
teal5Options = pt.CompileOptions(version=5)


def test_ecdsa_decompress():
    compressed_pubkey = pt.Bytes("XY")
    pubkey = pt.EcdsaDecompress(pt.EcdsaCurve.Secp256k1, compressed_pubkey)
    assert pubkey.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(compressed_pubkey, pt.Op.byte, '"XY"'),
            pt.TealOp(
                pubkey, pt.Op.ecdsa_pk_decompress, pt.EcdsaCurve.Secp256k1.arg_name
            ),
            pt.TealOp(
                pubkey.output_slots[1].store(), pt.Op.store, pubkey.output_slots[1]
            ),
            pt.TealOp(
                pubkey.output_slots[0].store(), pt.Op.store, pubkey.output_slots[0]
            ),
        ]
    )

    actual, _ = pubkey.__teal__(teal5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    # compile without errors this is necessary so assembly is also tested
    pt.compileTeal(pt.Seq(pubkey, pt.Approve()), pt.Mode.Application, version=5)


def test_ecdsa_recover():
    args = [pt.Bytes("data"), pt.Int(1), pt.Bytes("sigA"), pt.Bytes("sigB")]
    pubkey = pt.EcdsaRecover(
        pt.EcdsaCurve.Secp256k1, args[0], args[1], args[2], args[3]
    )
    assert pubkey.type_of() == pt.TealType.none

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"data"'),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(args[2], pt.Op.byte, '"sigA"'),
            pt.TealOp(args[3], pt.Op.byte, '"sigB"'),
            pt.TealOp(pubkey, pt.Op.ecdsa_pk_recover, pt.EcdsaCurve.Secp256k1.arg_name),
            pt.TealOp(
                pubkey.output_slots[1].store(), pt.Op.store, pubkey.output_slots[1]
            ),
            pt.TealOp(
                pubkey.output_slots[0].store(), pt.Op.store, pubkey.output_slots[0]
            ),
        ]
    )

    actual, _ = pubkey.__teal__(teal5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    # compile without errors this is necessary so assembly is also tested
    pt.compileTeal(pt.Seq(pubkey, pt.Approve()), pt.Mode.Application, version=5)


def test_ecdsa_verify_basic():
    args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
    pubkey = (pt.Bytes("X"), pt.Bytes("Y"))
    expr = pt.EcdsaVerify(pt.EcdsaCurve.Secp256k1, args[0], args[1], args[2], pubkey)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"data"'),
            pt.TealOp(args[1], pt.Op.byte, '"sigA"'),
            pt.TealOp(args[2], pt.Op.byte, '"sigB"'),
            pt.TealOp(pubkey[0], pt.Op.byte, '"X"'),
            pt.TealOp(pubkey[1], pt.Op.byte, '"Y"'),
            pt.TealOp(expr, pt.Op.ecdsa_verify, pt.EcdsaCurve.Secp256k1.arg_name),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    assert actual == expected

    # compile without errors this is necessary so assembly is also tested
    pt.compileTeal(pt.Seq(pt.Pop(expr), pt.Approve()), pt.Mode.Application, version=5)


def test_ecdsa_verify_compressed_pk():
    args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
    compressed_pubkey = pt.Bytes("XY")
    pubkey = pt.EcdsaDecompress(pt.EcdsaCurve.Secp256k1, compressed_pubkey)
    expr = pt.EcdsaVerify(pt.EcdsaCurve.Secp256k1, args[0], args[1], args[2], pubkey)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(compressed_pubkey, pt.Op.byte, '"XY"'),
            pt.TealOp(
                pubkey, pt.Op.ecdsa_pk_decompress, pt.EcdsaCurve.Secp256k1.arg_name
            ),
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
            pt.TealOp(expr, pt.Op.ecdsa_verify, pt.EcdsaCurve.Secp256k1.arg_name),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    # compile without errors this is necessary so assembly is also tested
    pt.compileTeal(pt.Seq(pt.Pop(expr), pt.Approve()), pt.Mode.Application, version=5)


def test_ecdsa_verify_recovered_pk():
    args = [pt.Bytes("data"), pt.Int(1), pt.Bytes("sigA"), pt.Bytes("sigB")]
    pubkey = pt.EcdsaRecover(
        pt.EcdsaCurve.Secp256k1, args[0], args[1], args[2], args[3]
    )
    expr = pt.EcdsaVerify(pt.EcdsaCurve.Secp256k1, args[0], args[2], args[3], pubkey)
    assert expr.type_of() == pt.TealType.uint64

    expected = pt.TealSimpleBlock(
        [
            pt.TealOp(args[0], pt.Op.byte, '"data"'),
            pt.TealOp(args[1], pt.Op.int, 1),
            pt.TealOp(args[2], pt.Op.byte, '"sigA"'),
            pt.TealOp(args[3], pt.Op.byte, '"sigB"'),
            pt.TealOp(pubkey, pt.Op.ecdsa_pk_recover, pt.EcdsaCurve.Secp256k1.arg_name),
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
            pt.TealOp(expr, pt.Op.ecdsa_verify, pt.EcdsaCurve.Secp256k1.arg_name),
        ]
    )

    actual, _ = expr.__teal__(teal5Options)
    actual.addIncoming()
    actual = pt.TealBlock.NormalizeBlocks(actual)

    with pt.TealComponent.Context.ignoreExprEquality():
        assert actual == expected

    # compile without errors this is necessary so assembly is also tested
    pt.compileTeal(pt.Seq(pt.Pop(expr), pt.Approve()), pt.Mode.Application, version=5)


def test_ecdsa_invalid():
    with pytest.raises(pt.TealTypeError):
        args = [pt.Bytes("data"), pt.Bytes("1"), pt.Bytes("sigA"), pt.Bytes("sigB")]
        pt.EcdsaRecover(pt.EcdsaCurve.Secp256k1, args[0], args[1], args[2], args[3])

    with pytest.raises(pt.TealTypeError):
        pt.EcdsaDecompress(pt.EcdsaCurve.Secp256k1, pt.Int(1))

    with pytest.raises(pt.TealTypeError):
        args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
        pubkey = (pt.Bytes("X"), pt.Int(1))
        pt.EcdsaVerify(pt.EcdsaCurve.Secp256k1, args[0], args[1], args[2], pubkey)

    with pytest.raises(pt.TealTypeError):
        args = [pt.Bytes("data"), pt.Int(1), pt.Bytes("sigB")]
        pubkey = (pt.Bytes("X"), pt.Bytes("Y"))
        pt.EcdsaVerify(pt.EcdsaCurve.Secp256k1, args[0], args[1], args[2], pubkey)

    with pytest.raises(pt.TealTypeError):
        args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
        compressed_pk = pt.Bytes("XY")
        pubkey = pt.MultiValue(
            pt.Op.ecdsa_pk_decompress,
            [pt.TealType.uint64, pt.TealType.bytes],
            immediate_args=[pt.EcdsaCurve.Secp256k1],
            args=[compressed_pk],
        )
        pt.EcdsaVerify(pt.EcdsaCurve.Secp256k1, args[0], args[1], args[2], pubkey)

    with pytest.raises(pt.TealInputError):
        args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
        pubkey = (pt.Bytes("X"), pt.Bytes("Y"))
        expr = pt.EcdsaVerify(
            pt.EcdsaCurve.Secp256k1, args[0], args[1], args[2], pubkey
        )

        expr.__teal__(teal4Options)

    with pytest.raises(pt.TealTypeError):
        args = [pt.Bytes("data"), pt.Bytes("sigA"), pt.Bytes("sigB")]
        pubkey = (pt.Bytes("X"), pt.Bytes("Y"))
        expr = pt.EcdsaVerify(5, args[0], args[1], args[2], pubkey)
