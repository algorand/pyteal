from typing import TYPE_CHECKING
from enum import Enum

from pyteal.ast.expr import Expr

from pyteal.ir import Op, TealBlock, TealOp
from pyteal.types import TealType, require_type
from pyteal.errors import verifyFieldVersion, verifyProgramVersion

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class EllipticCurve(Enum):
    # fmt: off
    #            id | name         | min version
    BN254g1 =     (0, "BN254g1",     10)
    BN254g2 =     (1, "BN254g2",     10)
    BLS12_381g1 = (2, "BLS12_381g1", 10)
    BLS12_381g2 = (3, "BLS12_381g2", 10)
    # fmt: on

    def __init__(self, id: int, name: str, min_version: int) -> None:
        self.id = id
        self.arg_name = name
        self.min_version = min_version


class EcOperation(Expr):
    def __init__(
        self, op: Op, curve: EllipticCurve, args: list[Expr], return_type: TealType
    ) -> None:
        super().__init__()
        self.op = op
        assert curve in EllipticCurve
        self.curve = curve
        for arg in args:
            require_type(arg, TealType.bytes)
        self.args = args
        self.return_type = return_type

    def __teal__(self, options: "CompileOptions"):
        verifyProgramVersion(
            self.op.min_version,
            options.version,
            f"Program version too low to use op {self.op}",
        )

        verifyFieldVersion(self.curve.arg_name, self.curve.min_version, options.version)

        op = TealOp(self, self.op, self.curve.arg_name)
        return TealBlock.FromOp(options, op, *self.args)

    def __str__(self):
        return f"(EcOperation {self.op} {self.curve} {self.args})"

    def type_of(self):
        return self.return_type

    def has_return(self):
        return False


def EcAdd(curve: EllipticCurve, a: Expr, b: Expr) -> Expr:
    """Add two points on the given elliptic curve.

    Args:
        curve: The elliptic curve to use.
        a: The first point to add. Must evaluate to bytes.
        b: The second point to add. Must evaluate to bytes.

    Returns:
        An expression which evaluates to the sum of the two points on the given
        curve.
    """
    return EcOperation(Op.ec_add, curve, [a, b], TealType.bytes)


def EcScalarMul(curve: EllipticCurve, point: Expr, scalar: Expr) -> Expr:
    """Multiply a point on the given elliptic curve by a scalar.

    Args:
        curve: The elliptic curve to use.
        point: The point to multiply. Must evaluate to bytes.
        scalar: The scalar to multiply by, encoded as a big-endian unsigned
            integer. Must evaluate to bytes. Fails if this value exceeds 32 bytes.

    Returns:
        An expression which evaluates to the product of the point and scalar on
        the given curve.
    """
    return EcOperation(Op.ec_scalar_mul, curve, [point, scalar], TealType.bytes)


def EcPairingCheck(curve: EllipticCurve, a: Expr, b: Expr) -> Expr:
    """Check the pairing of two points on the given elliptic curve.

    Args:
        curve: The elliptic curve to use.
        a: The first point to check. Must evaluate to bytes.
        b: The second point to check. Must evaluate to bytes.

    Returns:
        An expression which evaluates to 1 if the product of the pairing of each
        point in `a` with its respective point in `b` is equal to the identity
        element of the target group. Otherwise, evaluates to 0.
    """
    return EcOperation(Op.ec_pairing_check, curve, [a, b], TealType.uint64)


def EcMultiScalarMul(curve: EllipticCurve, a: Expr, b: Expr) -> Expr:
    """Multiply a point on the given elliptic curve by a series of scalars.

    Args:
        curve: The elliptic curve to use.
        a: The point to multiply. Must evaluate to bytes.
        b: A list of concatenated, big-endian, 32-byte scalar integers to
            multiply by.

    Returns:
        An expression that evaluates to curve point :code:`b_0a_0 + b_1a_1 + b_2a_2 + ... + b_Na_N`.
    """
    return EcOperation(Op.ec_multi_scalar_mul, curve, [a, b], TealType.bytes)


def EcSubgroupCheck(curve: EllipticCurve, a: Expr) -> Expr:
    """Check if a point is in the main prime-order subgroup of the given elliptic curve.

    Args:
        curve: The elliptic curve to use.
        a: The point to check. Must evaluate to bytes.

    Returns:
        An expression that evaluates to 1 if the point is in the main prime-order
        subgroup of the curve (including the point at infinity) else 0. Program
        fails if the point is not in the curve at all.
    """
    return EcOperation(Op.ec_subgroup_check, curve, [a], TealType.uint64)


def EcMapTo(curve: EllipticCurve, a: Expr) -> Expr:
    """Map field element `a` to group `curve`.

    Args:
        curve: The elliptic curve to use.
        a: The field element to map. Must evaluate to bytes.

    Returns:
        An expression that evaluates to the mapped point.
    """
    return EcOperation(Op.ec_map_to, curve, [a], TealType.bytes)
