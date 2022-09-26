from typing import TYPE_CHECKING

from plum import dispatch

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
    _hi_expr: Expr | Int
    _lo_expr: Expr | Int

    @classmethod
    def FromInt(cls, py_int: int) -> "WideInt":  # overload_1
        if py_int < 0 or py_int > 2**128 - 1:
            raise TealInputError("WideInt value must be between 0 and 2**128-1")

        cls._hi_expr = Int(py_int >> 64)
        cls._lo_expr = Int(py_int & 0xFFFFFFFFFFFFFFFF)  # 64-bit mask
        return cls.FromExprExpr(cls._hi_expr, cls._lo_expr)

    @classmethod
    def FromExprExpr(cls, expr_high: Expr, expr_low: Expr) -> "WideInt":
        require_type(expr_high, TealType.uint64)
        require_type(expr_low, TealType.uint64)
        cls._hi_expr = expr_high
        cls._lo_expr = expr_low
        return cls(ScratchSlot(), ScratchSlot())

    @dispatch
    def __init__(self, py_int: int):  # type: ignore
        wide_int = self.FromInt(py_int)
        self.hi = wide_int.hi
        self.lo = wide_int.lo

    @dispatch
    def __init__(self, expr_high: Expr, expr_low: Expr):  # type: ignore
        wide_int = self.FromExprExpr(expr_high, expr_low)
        self.hi = wide_int.hi
        self.lo = wide_int.lo

    @dispatch
    def __init__(self, slot_hi: ScratchSlot, slot_lo: ScratchSlot) -> None:
        # FIX: use `Expr` instead of `Int` in docstring
        """
        WideInt(num: int) -> WideInt
        WideInt(expr_high: Expr, expr_low: Expr) -> WideInt

        Create a new WideInt.

        For int:
            Pass the int as the only argument. For example, ``WideInt((1<<64)+1)``.
        For two Int() objects:
            Pass the two Int. They must have type ``TealType.uint64`` For example, ``WideInt(Int(1),Int(1))``.
        """
        super().__init__()
        self.hi = slot_hi
        self.lo = slot_lo
        self.hi.store(self._hi_expr)
        self.lo.store(self._lo_expr)

    def __str__(self):
        # TODO: not sure how this works
        return "(wide_int hi:{} lo:{})".format(self.hi, self.lo)

    def __teal__(self, options: "CompileOptions"):
        # TODO: compile check
        store_lo = self.lo.store(self._lo_expr).__teal__(options)
        store_hi = self.hi.store(self._hi_expr).__teal__(options)

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
