from typing import Optional, TYPE_CHECKING

from .tealcomponent import TealComponent
if TYPE_CHECKING:
    from ..ast import Expr
class TealLabel(TealComponent):

    def __init__(self, expr: Optional['Expr'], label: str) -> None:
        super().__init__(expr)
        self.label = label
    
    def assemble(self) -> str:
        return self.label + ":"
    
    def __repr__(self) -> str:
        return "TealLabel({}, {})".format(self.expr, repr(self.label))
    
    def __hash__(self) -> int:
        return self.label.__hash__()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealLabel):
            return False
        if TealComponent.Context.checkExpr and self.expr is not other.expr:
            return False
        return self.label == other.label

TealLabel.__module__ = "pyteal"
