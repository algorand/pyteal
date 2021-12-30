from typing import TYPE_CHECKING

from pyteal.types import TealType

from ..types import TealType
from ..ir import TealOp, Op, TealBlock
from .leafexpr import LeafExpr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class Method(LeafExpr):
    """An expression that represents an ABI method selector"""

    def __init__(self, methodName: str) -> None:
        """Create a new method selector for ABI method call.

        Args:
            methodName: A string containing a valid ABI method signature
        """
        super().__init__()
        # TODO do we need to check method name validity?
        self.methodName = methodName

    def __teal__(self, options: "CompileOptions"):
        op = TealOp(self, Op.method, self.methodName)
        return TealBlock.FromOp(options, op)

    def __str__(self) -> str:
        return "(method: {})".format(self.methodName)

    def type_of(self) -> TealType:
        return TealType.bytes


Method.__module__ = "pyteal"
