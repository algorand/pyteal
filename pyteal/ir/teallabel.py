from typing import Optional, TYPE_CHECKING

from .tealcomponent import TealComponent
from .labelref import LabelReference

if TYPE_CHECKING:
    from ..ast import Expr


class TealLabel(TealComponent):
    def __init__(
        self, expr: Optional["Expr"], label: LabelReference, comment: str = None
    ) -> None:
        super().__init__(expr)
        self.label = label
        self.comment = comment

    def getLabelRef(self) -> LabelReference:
        return self.label

    def assemble(self) -> str:
        comment = "\n// {}\n".format(self.comment) if self.comment is not None else ""
        return "{}{}:".format(comment, self.label.getLabel())

    def __repr__(self) -> str:
        return "TealLabel({}, {}, {})".format(
            self.expr, repr(self.label), repr(self.comment)
        )

    def __hash__(self) -> int:
        return hash((self.label, self.comment))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealLabel):
            return False
        if TealComponent.Context.checkExpr and self.expr is not other.expr:
            return False
        return self.label == other.label and self.comment == other.comment


TealLabel.__module__ = "pyteal"
