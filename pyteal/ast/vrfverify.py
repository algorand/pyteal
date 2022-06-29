from enum import Enum

from pyteal.types import TealType, require_type
from pyteal.errors import verifyFieldVersion
from pyteal.ir import Op
from pyteal.ast.multi import MultiValue
from pyteal.ast.expr import Expr


class VrfVerifyStandard(Enum):
    # fmt: off
    #           id  |   name   | min version
    algorand =  (0, "VrfAlgorand",  7)  # noqa: E222
    chainlink = (1, "VrfChainlink", 7)
    # fmt: on

    def __init__(self, id: int, name: str, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.min_version = min_version


VrfVerifyStandard.__module__ = "pyteal"


class VrfVerify(MultiValue):
    """An expression that verifies the proof of a message against a public key."""

    def __init__(
        self, standard: VrfVerifyStandard, message: Expr, proof: Expr, public_key: Expr
    ) -> None:
        require_type(message, TealType.bytes)
        require_type(proof, TealType.bytes)
        require_type(public_key, TealType.bytes)

        self.standard = standard

        super().__init__(
            Op.vrf_verify,
            [TealType.bytes, TealType.uint64],
            immediate_args=[standard.arg_name],
            args=[message, proof, public_key],
            compile_check=lambda options: verifyFieldVersion(
                standard.arg_name, standard.min_version, options.version
            ),
        )

    def __str__(self):
        return "(VrfVerify {})".format(self.standard.arg_name)

    @classmethod
    def algorand(cls, message: Expr, proof: Expr, public_key: Expr) -> "VrfVerify":
        """Verifies the proof of a message against a public key using the Algorand VRF standard.

        Args:
            message: The message to verify.
            proof: The proof of the message.
            public_key: The public key to use to verify the proof.

        Returns:
            A MultiValue expression representing the VRF output and a verification flag.
        """
        return cls(VrfVerifyStandard.algorand, message, proof, public_key)

    @classmethod
    def chainlink(cls, message: Expr, proof: Expr, public_key: Expr) -> "VrfVerify":
        """Verifies the proof of a message against a public key using the Chainlink VRF standard.

        Args:
            message: The message to verify.
            proof: The proof of the message.
            public_key: The public key to use to verify the proof.

        Returns:
            A MultiValue expression representing the VRF output and a verification flag.
        """
        return cls(VrfVerifyStandard.chainlink, message, proof, public_key)


VrfVerify.__module__ = "pyteal"
