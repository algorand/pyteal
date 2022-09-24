from typing import TYPE_CHECKING
from pyteal.ast.multi import MultiValue

from pyteal.types import TealType, require_type
from pyteal.ast.expr import Expr
from pyteal.ir import Op

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


"""Binary MultiValue operations"""


def AddW(adder: Expr, adder_: Expr) -> MultiValue:
    """Add two 64-bit integers.

    Produces a MultiValue with two outputs: the sum and the carry bit.

    Args:
        adder: Must evaluate to uint64.
        adder_: Must evaluate to uint64.
    """

    # Should this be
    require_type(adder, TealType.uint64)
    require_type(adder_, TealType.uint64)

    return MultiValue(Op.addw, [TealType.uint64, TealType.uint64], args=[adder, adder_])
