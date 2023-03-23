from enum import Enum
from typing import TYPE_CHECKING

from algosdk.constants import ZERO_ADDRESS

from pyteal.types import TealType, valid_tmpl
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.leafexpr import LeafExpr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class TmplKind(Enum):
    Int = 0
    Bytes = 1
    Addr = 2


class Tmpl(LeafExpr):
    """Template expression for creating placeholder values."""

    _session_templates: dict[str, TmplKind] = {}

    def __init__(self, op: Op, type: TealType, name: str, kind: TmplKind) -> None:
        super().__init__()
        valid_tmpl(name)
        self.op = op
        self.type = type
        self.name = name

        self._session_templates[name] = kind

    def __str__(self):
        return "(Tmpl {} {})".format(self.op, self.name)

    def __teal__(self, options: "CompileOptions"):
        op = TealOp(self, self.op, self.name)
        return TealBlock.FromOp(options, op)

    def type_of(self):
        return self.type

    @classmethod
    def session_templates(cls) -> list[str]:
        return list(cls._session_templates.keys())

    @classmethod
    def clear_session_templates(cls):
        """Clear all session templates."""
        cls._session_templates = {}

    @classmethod
    def Int(cls, placeholder: str):
        """Create a new Int template.

        Args:
            placeholder: The name to use for this template variable. Must start with `TMPL_` and
                only consist of uppercase alphanumeric characters and underscores.
        """
        return cls(Op.int, TealType.uint64, placeholder, TmplKind.Int)

    @classmethod
    def Bytes(cls, placeholder: str):
        """Create a new Bytes template.

        Args:
            placeholder: The name to use for this template variable. Must start with `TMPL_` and
                only consist of uppercase alphanumeric characters and underscores.
        """
        return cls(Op.byte, TealType.bytes, placeholder, TmplKind.Bytes)

    @classmethod
    def Addr(cls, placeholder: str):
        """Create a new Addr template.

        Args:
            placeholder: The name to use for this template variable. Must start with `TMPL_` and
                only consist of uppercase alphanumeric characters and underscores.
        """
        return cls(Op.addr, TealType.bytes, placeholder, TmplKind.Addr)

    @classmethod
    def zero(cls, placeholder) -> str:
        """Return a zero value for the given template placeholder."""
        if placeholder not in cls._session_templates:
            raise ValueError(f"Unknown template: {placeholder}")

        match (kind := cls._session_templates[placeholder]):
            case TmplKind.Int:
                return "0"
            case TmplKind.Bytes:
                return "0x00"
            case TmplKind.Addr:
                return ZERO_ADDRESS
            case _:
                raise ValueError(f"Unknown template kind: {kind}")


Tmpl.__module__ = "pyteal"
