from pyteal import (
    Bytes,
    EcdsaCurve,
    EcdsaDecompress,
    EcdsaRecover,
    EcdsaVerify,
    Int,
    And,
    Subroutine,
    Sha512_256,
    Mode,
    TealType,
)

from tests.blackbox import (
    Blackbox,
    PyTealDryRunExecutor,
)


def test_verify():
    @Blackbox(input_types=[])
    @Subroutine(TealType.uint64)
    def verify():
        return EcdsaVerify(
            EcdsaCurve.Secp256k1,
            Sha512_256(Bytes("testdata")),
            Bytes(
                "base16",
                "33602297203d2753372cea7794ffe1756a278cbc4907b15a0dd132c9fb82555e",
            ),
            Bytes(
                "base16",
                "20f112126cf3e2eac6e8d4f97a403d21bab07b8dbb77154511bb7b07c0173195",
            ),
            (
                Bytes(
                    "base16",
                    "d6143a58c90c06b594e4414cb788659c2805e0056b1dfceea32c03f59efec517",
                ),
                Bytes(
                    "base16",
                    "00bd2400c479efe5ea556f37e1dc11ccb20f1e642dbfe00ca346fffeae508298",
                ),
            ),
        )

    args = []
    app_result = PyTealDryRunExecutor(verify, Mode.Application).dryrun(
        args, compiler_version=5
    )

    assert app_result.stack_top() == 1, app_result.report(
        args, "stack_top() is not equal to 1, indicating ecdsa verification failed."
    )

    @Blackbox(input_types=[])
    @Subroutine(TealType.uint64)
    def verify_fail():
        return EcdsaVerify(
            EcdsaCurve.Secp256k1,
            Sha512_256(Bytes("testdata")),
            Bytes(
                "base16",
                "13602297203d2753372cea7794ffe1756a278cbc4907b15a0dd132c9fb82555e",
            ),
            Bytes(
                "base16",
                "20f112126cf3e2eac6e8d4f97a403d21bab07b8dbb77154511bb7b07c0173195",
            ),
            (
                Bytes(
                    "base16",
                    "d6143a58c90c06b594e4414cb788659c2805e0056b1dfceea32c03f59efec517",
                ),
                Bytes(
                    "base16",
                    "00bd2400c479efe5ea556f37e1dc11ccb20f1e642dbfe00ca346fffeae508298",
                ),
            ),
        )

    args = []
    app_result = PyTealDryRunExecutor(verify_fail, Mode.Application).dryrun(
        args, compiler_version=5
    )

    assert app_result.stack_top() == 0, app_result.report(
        args,
        "stack_top() is not equal to 0, indicating ecdsa verification succeeded when a failure was expected.",
    )


def test_decompress():
    @Blackbox(input_types=[])
    @Subroutine(TealType.uint64)
    def decompress():
        return EcdsaDecompress(
            EcdsaCurve.Secp256k1,
            Bytes(
                "base16",
                "03bd83d54f6a799d05b496653b64bc933e17a898cda4793fe662d50645ecc977d1",
            ),
        ).outputReducer(
            lambda x, y: And(
                x
                == Bytes(
                    "base16",
                    "bd83d54f6a799d05b496653b64bc933e17a898cda4793fe662d50645ecc977d1",
                ),
                y
                == Bytes(
                    "base16",
                    "d4f3063a1ffca4139ea921b5696a6597640289175afece3bc38217a29d6270f9",
                ),
            )
        )

    args = []
    app_result = PyTealDryRunExecutor(decompress, Mode.Application).dryrun(
        args, compiler_version=5
    )

    assert app_result.stack_top() == 1, app_result.report(
        args, "stack_top() is not equal to 1, indicating ecdsa verification failed."
    )


def test_recover():
    @Blackbox(input_types=[])
    @Subroutine(TealType.uint64)
    def recover():
        return EcdsaRecover(
            EcdsaCurve.Secp256k1,
            Sha512_256(Bytes("testdata")),
            Int(1),
            Bytes(
                "base16",
                "cabed943e1403fb93b388174c59a52c759b321855f2d7c4fcc23c99a8a6dce79",
            ),
            Bytes(
                "base16",
                "56192820dde344c32f81450db05e51c6a6f45a2a2db229f657d2c040baf31537",
            ),
        ).outputReducer(
            lambda x, y: And(
                x
                == Bytes(
                    "base16",
                    "71539e0c7a6902a3f5413d6e28a455b2a14316fcf0f6b21193343b3b9d455053",
                ),
                y
                == Bytes(
                    "base16",
                    "fa49ccd95795c7c9a447fdeee83a2193472507a4e41a47e0d50eeeb547b74c51",
                ),
            )
        )

    args = []
    app_result = PyTealDryRunExecutor(recover, Mode.Application).dryrun(
        args, compiler_version=5
    )

    assert app_result.stack_top() == 1, app_result.report(
        args, "stack_top() is not equal to 1, indicating ecdsa verification failed."
    )
