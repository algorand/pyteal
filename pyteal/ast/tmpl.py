from typing import TYPE_CHECKING

from pyteal.types import TealType, valid_tmpl
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.leafexpr import LeafExpr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Tmpl(LeafExpr):
    """Template expression for creating placeholder values."""

    def __init__(self, op: Op, type: TealType, name: str) -> None:
        super().__init__()
        valid_tmpl(name)
        self.op = op
        self.type = type
        self.name = name

    def __str__(self):
        return "(Tmpl {} {})".format(self.op, self.name)

    def __teal__(self, options: "CompileOptions"):
        op = TealOp(self, self.op, self.name)
        return TealBlock.FromOp(options, op)

    def type_of(self):
        return self.type

    @classmethod
    def Int(cls, placeholder: str):
        """Create a new Int template.

        Args:
            placeholder: The name to use for this template variable. Must start with `TMPL_` and
                only consist of uppercase alphanumeric characters and underscores.
        """
        return cls(Op.int, TealType.uint64, placeholder)

    @classmethod
    def Bytes(cls, placeholder: str):
        """Create a new Bytes template.

        Args:
            placeholder: The name to use for this template variable. Must start with `TMPL_` and
                only consist of uppercase alphanumeric characters and underscores.
        """
        return cls(Op.byte, TealType.bytes, placeholder)

    @classmethod
    def Addr(cls, placeholder: str):
        """Create a new Addr template.

        Args:
            placeholder: The name to use for this template variable. Must start with `TMPL_` and
                only consist of uppercase alphanumeric characters and underscores.
        """
        return cls(Op.addr, TealType.bytes, placeholder)


Tmpl.__module__ = "pyteal"
