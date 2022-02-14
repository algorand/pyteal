from typing import TYPE_CHECKING
from pyteal.errors import TealInputError

from pyteal.types import TealType

from ..types import TealType
from ..ir import TealOp, Op, TealBlock
from .leafexpr import LeafExpr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class MethodSignature(LeafExpr):
    """An expression that represents an ABI method selector"""

    def __init__(self, methodName: str) -> None:
        """Create a new method selector for ABI method call.

        Args:
            methodName: A string containing a valid ABI method signature
        """
        super().__init__()
        if type(methodName) is not str:
            raise TealInputError(
                "invalid input type {} to Method".format(type(methodName))
            )
        elif len(methodName) == 0:
            raise TealInputError("invalid input empty string to Method")
        self.methodName = methodName

    def __teal__(self, options: "CompileOptions"):
        op = TealOp(self, Op.method_signature, '"{}"'.format(self.methodName))
        return TealBlock.FromOp(options, op)

    def __str__(self) -> str:
        return "(method: {})".format(self.methodName)

    def type_of(self) -> TealType:
        return TealType.bytes


MethodSignature.__module__ = "pyteal"
