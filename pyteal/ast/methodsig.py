from typing import TYPE_CHECKING

from pyteal.errors import TealInputError
from pyteal.types import TealType
from pyteal.ir import TealOp, Op, TealBlock

from pyteal.ast.leafexpr import LeafExpr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


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
        return "(MethodSignature '{}')".format(self.methodName)

    def type_of(self) -> TealType:
        return TealType.bytes


MethodSignature.__module__ = "pyteal"
