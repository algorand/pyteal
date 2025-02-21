from typing import TYPE_CHECKING
from enum import Enum

from pyteal.types import TealType, require_type
from pyteal.errors import verifyFieldVersion, verifyProgramVersion
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class MimcConfig(Enum):
    # fmt: off
    #           id  |   name   | min version
    bn254mp110 =  (0, "BN254Mp110",  11)  # noqa: E222
    bls12_381mp111 = (1, "BLS12_381Mp111", 11)  # noqa: E222
    # fmt: on

    def __init__(self, id: int, name: str, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.min_version = min_version


MimcConfig.__module__ = "pyteal"


class MiMC(Expr):
    """An expression that computes the MiMC hash on a byte string message."""

    def __init__(self, config: MimcConfig, message: Expr) -> None:
        super().__init__()

        self.config = config

        require_type(message, TealType.bytes)
        self.message = message

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            Op.mimc.min_version,
            options.version,
            "Program version too low to use op mimc",
        )

        verifyFieldVersion(
            self.config.arg_name, self.config.min_version, options.version
        )

        op = TealOp(self, Op.mimc, self.config.arg_name)
        return TealBlock.FromOp(options, op, self.message)

    def __str__(self):
        return "(MiMC {})".format(self.config.arg_name)

    def type_of(self) -> TealType:
        return TealType.bytes

    def has_return(self):
        return False

    @classmethod
    def bn254mp110(cls, message: Expr) -> Expr:
        """Verifies the proof of a message against a public key using the Algorand VRF standard.

        Args:
            message: The message to hash.

        Returns:
            A 32-byte hash of message
        """
        return cls(MimcConfig.bn254mp110, message)

    @classmethod
    def bls12_381mp111(cls, message: Expr) -> Expr:
        """Verifies the proof of a message against a public key using the Chainlink VRF standard.

        Args:
            message: The message to hash.

        Returns:
            A 32-byte hash of message
        """
        return cls(MimcConfig.bls12_381mp111, message)


MiMC.__module__ = "pyteal"
