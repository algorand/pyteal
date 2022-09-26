from typing import TYPE_CHECKING, overload

from pyteal.ast.expr import Expr
from pyteal.ast.int import Int
from pyteal.ast.leafexpr import LeafExpr
from pyteal.ast.scratch import ScratchSlot
from pyteal.errors import TealInputError
from pyteal.types import TealType, require_type

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class WideInt(LeafExpr):
    """Represents a wide integer value."""

    hi: ScratchSlot
    lo: ScratchSlot
    _hi_int: Expr | Int
    _lo_int: Expr | Int

    @overload
    def __init__(self, arg1: int) -> None:  # overload_1
        pass

    @overload
    def __init__(self, arg1: Expr, arg2: Expr) -> None:  # overload_2
        pass

    def __init__(self, arg1: int | Expr, arg2: None | Expr = None) -> None:
        """
        WideInt(arg1: int) -> None
        WideInt(arg1: Expr, arg2: Expr) -> None

        Create a new WideInt.

        For int:
            Pass the int as the only argument. For example, ``WideInt((1<<64)+1)``.
        For two Int() objects:
            Pass the two Int. They must have type ``TealType.uint64`` For example, ``WideInt(Int(1),Int(1))``.
        """

        super().__init__()
        correct_type = (isinstance(arg1, int) and arg2 is None) or (
            isinstance(arg1, Expr) and isinstance(arg2, Expr)
        )
        if not correct_type:
            raise TealInputError(
                f"WideInt() requires `int` or `Expr, Expr`, got {arg1} of {type(arg1)} and {arg2} of {type(arg2)}"
            )

        if isinstance(arg1, int):
            self._hi_int = Int(arg1 >> 64)
            self._lo_int = Int(arg1 & 0xFFFFFFFFFFFFFFFF)  # 64-bit mask
        elif isinstance(arg1, Expr) and isinstance(arg2, Expr):
            require_type(arg1, TealType.uint64)
            require_type(arg2, TealType.uint64)
            self._hi_int = arg1
            self._lo_int = arg2
        # don't need else because of correct_type check

        self.hi = ScratchSlot()
        self.lo = ScratchSlot()
        self.hi.store(self._hi_int)
        self.lo.store(self._lo_int)

    def __str__(self):
        # TODO: not sure how this works
        return "(wide_int {} {})".format(self.hi.load(), self.lo.load())

    def __teal__(self, options: "CompileOptions"):
        # TODO: compile check
        store_lo = self.lo.store(self._lo_int).__teal__(options)
        store_hi = self.hi.store(self._hi_int).__teal__(options)

        # for Int.__teal__(), [0] and [1] are the same, but not for store.

        # this is reversed
        start = store_lo[0]
        end = store_lo[1]
        end.setNextBlock(store_hi[0])
        end = store_hi[1]

        return start, end

    def type_of(self):
        return TealType.none
        # [TealType.uint64, TealType.uint64] matches MultiValue.types but fails test

    @property
    def high(self):
        return self.hi  # should add? : .load()

    @property
    def low(self):
        return self.lo  # should add? : .load()


WideInt.__module__ = "pyteal"
