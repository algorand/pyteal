from .expr import Expr


class LeafExpr(Expr):
    """Leaf expression base class."""

    def has_return(self):
        return False


LeafExpr.__module__ = "pyteal"
