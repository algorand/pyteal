from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple, List, TYPE_CHECKING

from ..types import TealType
from ..ir import TealBlock, TealSimpleBlock

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class Expr(ABC):
    """Abstract base class for PyTeal expressions."""

    def __init__(self):
        import traceback

        self.trace = traceback.format_stack()[0:-1]

    def getDefinitionTrace(self) -> List[str]:
        return self.trace

    @abstractmethod
    def type_of(self) -> TealType:
        """Get the return type of this expression."""
        pass

    @abstractmethod
    def has_return(self) -> bool:
        """Check if this expression always returns from the current subroutine or program."""
        pass

    @abstractmethod
    def __str__(self) -> str:
        """Get a string representation of this experssion."""
        pass

    @abstractmethod
    def __teal__(self, options: "CompileOptions") -> Tuple[TealBlock, TealSimpleBlock]:
        """Assemble TEAL IR for this component and its arguments."""
        pass

    def __lt__(self, other):
        from .binaryexpr import Lt

        return Lt(self, other)

    def __gt__(self, other):
        from .binaryexpr import Gt

        return Gt(self, other)

    def __le__(self, other):
        from .binaryexpr import Le

        return Le(self, other)

    def __ge__(self, other):
        from .binaryexpr import Ge

        return Ge(self, other)

    def __eq__(self, other):
        from .binaryexpr import Eq

        return Eq(self, other)

    def __ne__(self, other):
        from .binaryexpr import Neq

        return Neq(self, other)

    def __add__(self, other):
        from .binaryexpr import Add

        return Add(self, other)

    def __sub__(self, other):
        from .binaryexpr import Minus

        return Minus(self, other)

    def __mul__(self, other):
        from .binaryexpr import Mul

        return Mul(self, other)

    def __truediv__(self, other):
        from .binaryexpr import Div

        return Div(self, other)

    def __mod__(self, other):
        from .binaryexpr import Mod

        return Mod(self, other)

    def __pow__(self, other):
        from .binaryexpr import Exp

        return Exp(self, other)

    def __invert__(self):
        from .unaryexpr import BitwiseNot

        return BitwiseNot(self)

    def __and__(self, other):
        from .binaryexpr import BitwiseAnd

        return BitwiseAnd(self, other)

    def __or__(self, other):
        from .binaryexpr import BitwiseOr

        return BitwiseOr(self, other)

    def __xor__(self, other):
        from .binaryexpr import BitwiseXor

        return BitwiseXor(self, other)

    def __lshift__(self, other):
        from .binaryexpr import ShiftLeft

        return ShiftLeft(self, other)

    def __rshift__(self, other):
        from .binaryexpr import ShiftRight

        return ShiftRight(self, other)

    def And(self, other: "Expr") -> "Expr":
        """Take the logical And of this expression and another one.

        This expression must evaluate to uint64.

        This is the same as using :func:`And()` with two arguments.
        """
        from .naryexpr import And

        return And(self, other)

    def Or(self, other: "Expr") -> "Expr":
        """Take the logical Or of this expression and another one.

        This expression must evaluate to uint64.

        This is the same as using :func:`Or()` with two arguments.
        """
        from .naryexpr import Or

        return Or(self, other)


Expr.__module__ = "pyteal"
