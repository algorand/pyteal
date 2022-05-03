from graviton.blackbox import DryRunExecutor
from pyteal.ast.bytes import Bytes
from pyteal.ast.ecdsa import EcdsaCurve, EcdsaVerify
from pyteal.ast.subroutine import Subroutine
from pyteal.ast.unaryexpr import Sha512_256
from pyteal.compiler.compiler import compileTeal
from pyteal.ir.ops import Mode
from pyteal.types import TealType

from tests.blackbox import (
    Blackbox,
    algod_with_assertion,
    blackbox_pyteal,
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

    approval_app = blackbox_pyteal(verify, Mode.Application)
    app_teal = compileTeal(approval_app(), Mode.Application, version=5)
    args = []
    algod = algod_with_assertion()
    app_result = DryRunExecutor.dryrun_app(algod, app_teal, args)

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

    approval_app = blackbox_pyteal(verify_fail, Mode.Application)
    app_teal = compileTeal(approval_app(), Mode.Application, version=5)
    args = []
    algod = algod_with_assertion()
    app_result = DryRunExecutor.dryrun_app(algod, app_teal, args)

    assert app_result.stack_top() == 0, app_result.report(
        args,
        "stack_top() is not equal to 0, indicating ecdsa verification succeeded when a failure was expected.",
    )
