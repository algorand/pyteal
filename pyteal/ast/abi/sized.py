from dataclasses import dataclass
from typing import Union
from .. import Expr
from ..assert_ import Assert
from pyteal.ast import Int, Seq, ScratchVar


@dataclass(frozen=True)
class SizedExpr:
    """Provides a wrapper class to tag `Expr`s with known ABI data sizes.

    Knowing the data size removes the need for a runtime `Assert` confirming it fits into the ScratchVar."""

    underlying: Expr

    @staticmethod
    def store_into(
        u: Union[Expr, "SizedExpr"], s: ScratchVar, supported_bit_size: int
    ) -> Expr:
        return (
            s.store(u.underlying)
            if isinstance(u, SizedExpr)
            else Seq(s.store(u), Assert(s.load() < Int(2 ** supported_bit_size)))
        )
