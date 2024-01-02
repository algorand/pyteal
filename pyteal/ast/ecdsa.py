from enum import Enum
from typing import Tuple, TYPE_CHECKING

from pyteal.ast.expr import Expr
from pyteal.ast.multi import MultiValue
from pyteal.errors import (
    TealTypeError,
    verifyFieldVersion,
    verifyProgramVersion,
    TealInputError,
)
from pyteal.ir import Op, TealBlock, TealOp
from pyteal.types import TealType, require_type

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


EcdsaPubkey = [TealType.bytes, TealType.bytes]


class EcdsaCurve(Enum):
    """Enum representing an elliptic curve specification used in ECDSA."""

    Secp256k1 = (0, "Secp256k1", 5)
    Secp256r1 = (1, "Secp256r1", 7)

    def __init__(self, id: int, name: str, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.min_version = min_version


class EcdsaVerifyExpr(Expr):
    """Implements basic ECDSA verification functionality

    This class shouldn't be directly used in a PyTeal program. The EcdsaVerify function
    should be used instead."""

    def __init__(
        self,
        curve: EcdsaCurve,
        data: Expr,
        sigA: Expr,
        sigB: Expr,
        pkX: Expr,
        pkY: Expr,
    ):
        super().__init__()
        require_type(data, TealType.bytes)
        require_type(sigA, TealType.bytes)
        require_type(sigB, TealType.bytes)
        require_type(pkX, TealType.bytes)
        require_type(pkY, TealType.bytes)

        self.op = Op.ecdsa_verify
        self.curve = curve
        self.args = [data, sigA, sigB, pkX, pkY]

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            self.op.min_version,
            options.version,
            "Program version too low to use op {}".format(self.op),
        )

        verifyFieldVersion(self.curve.arg_name, self.curve.min_version, options.version)

        return TealBlock.FromOp(
            options, TealOp(self, self.op, self.curve.arg_name), *self.args
        )

    def __str__(self):
        return "({} {} {} {} {} {} {})".format(self.op, self.curve, *self.args)

    def type_of(self):
        return TealType.uint64

    def has_return(self):
        return False


def EcdsaVerify(
    curve: EcdsaCurve,
    data: Expr,
    sigA: Expr,
    sigB: Expr,
    pubkey: Tuple[Expr, Expr] | MultiValue,
) -> Expr:
    """Verify an ECDSA signature.

    The public key argument can be represented as either a tuple of Byte expressions
    representing the (X,Y) point on the elliptic curve or a MultiValue expression returning
    two Byte expressions, ex. the value returned by EcdsaDecompress or EcdsaRecover. All byte
    arguments must be big endian encoded.

    Args:
        curve: Enum representing the ECDSA curve used for the signature and public key
        data: Hash value of the signed data. Must be 32 bytes long.
        sigA: First component of the signature. Must evaluate to bytes.
        sigB: Second component of the signature. Must evaluate to bytes.
        pubkey: Public key used to verify signature. Represented as either a tuple of expressions
            that must evaluate to bytes or as a MultiValue expression that returns two byte values.

    Returns:
        An expression evaluating to either 0 or 1 representing the success of verification
    """

    if not isinstance(curve, EcdsaCurve):
        raise TealTypeError(curve, EcdsaCurve)

    if isinstance(pubkey, MultiValue):
        if pubkey.types != EcdsaPubkey:
            raise TealTypeError(pubkey.types, EcdsaPubkey)

        return pubkey.outputReducer(
            lambda X, Y: EcdsaVerifyExpr(curve, data, sigA, sigB, X, Y)
        )

    return EcdsaVerifyExpr(curve, data, sigA, sigB, pubkey[0], pubkey[1])


def EcdsaDecompress(curve: EcdsaCurve, compressed_pk: Expr) -> MultiValue:
    """Decompress an ECDSA public key.
    Args:
        curve: Enum representing the ECDSA curve used for the public key
        compressed_pk: The compressed public key. Must be 33 bytes long and big endian encoded.
    Returns:
        A MultiValue expression representing the two components of the public key, big endian
        encoded.
    """

    if not isinstance(curve, EcdsaCurve):
        raise TealTypeError(curve, EcdsaCurve)

    require_type(compressed_pk, TealType.bytes)
    return MultiValue(
        Op.ecdsa_pk_decompress,
        EcdsaPubkey,
        immediate_args=[curve.arg_name],
        args=[compressed_pk],
        compile_check=lambda options: verifyFieldVersion(
            curve.arg_name, curve.min_version, options.version
        ),
    )


def EcdsaRecover(
    curve: EcdsaCurve, data: Expr, recovery_id: Expr, sigA: Expr, sigB: Expr
) -> MultiValue:
    """Recover an ECDSA public key from a signature.
    All byte arguments must be big endian encoded.
    Args:
        curve: Enum representing the ECDSA curve used for the public key
        data: Hash value of the signed data. Must be 32 bytes long.
        recovery_id: value used to extract public key from signature. Must evaluate to uint.
        sigA: First component of the signature. Must evaluate to bytes.
        sigB: Second component of the signature. Must evaluate to bytes.
    Returns:
        A MultiValue expression representing the two components of the public key, big endian
        encoded.
    """

    if not isinstance(curve, EcdsaCurve):
        raise TealTypeError(curve, EcdsaCurve)

    if curve != EcdsaCurve.Secp256k1:
        raise TealInputError("Recover only supports Secp256k1")

    require_type(data, TealType.bytes)
    require_type(recovery_id, TealType.uint64)
    require_type(sigA, TealType.bytes)
    require_type(sigB, TealType.bytes)
    return MultiValue(
        Op.ecdsa_pk_recover,
        EcdsaPubkey,
        immediate_args=[curve.arg_name],
        args=[data, recovery_id, sigA, sigB],
        compile_check=lambda options: verifyFieldVersion(
            curve.arg_name, curve.min_version, options.version
        ),
    )
