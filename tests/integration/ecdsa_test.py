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
            Bytes("sigA"),
            Bytes("sigB"),
            (Bytes("X"), Bytes("Y"))
        )

    approval_app = blackbox_pyteal(verify, Mode.Application)

    app_teal = compileTeal(approval_app(), Mode.Application, version=5)

    args = []

    algod = algod_with_assertion()
    app_result = DryRunExecutor.dryrun_app(algod, app_teal, args)

    assert app_result.status == "PASS"