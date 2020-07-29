from ..types import TealType, valid_tmpl
from ..errors import TealInternalError
from .leafexpr import LeafExpr

class Tmpl(LeafExpr):
    """Template expression for creating placeholder values."""

    def __init__(self, tmpl_v: str) -> None:
        valid_tmpl(tmpl_v)
        self.name = tmpl_v

    def __str__(self):
        return self.name

    def __teal__(self):
        raise TealInternalError("Tmpl is not expected here")

    def type_of(self):
        raise TealInternalError("Tmpl is not expected here")
