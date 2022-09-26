from typing import TYPE_CHECKING, overload, cast

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

    @overload
    def __init__(self, arg1: int):  # overload_1
        pass

    @overload
    def __init__(self, arg1: Expr, arg2: Expr):  # overload_2
        pass

    @overload
    def __init__(self, arg1: ScratchSlot, arg2: ScratchSlot) -> None:
        pass  # overload_3

    def __init__(
        self, arg1: int | Expr | ScratchSlot, arg2: Expr | ScratchSlot | None = None
    ):
        """
        WideInt(num: int) -> WideInt
        WideInt(expr_high: Expr, expr_low: Expr) -> WideInt
        WideInt(expr_high: ScratchSlot, expr_low: ScratchSlot) -> WideInt

        Create a new WideInt.

        For int:
            Pass the int as the only argument. For example, ``WideInt((1<<64)+1)``.
        For two Expr() objects:
            Pass two ``Expr``s. They must be of type ``TealType.uint64`` For example, ``WideInt(Int(1),Int(1))``.
        For two ScratchSlot() objects:
            Pass two ``ScratchSlot``s. For example, ``WideInt(ScratchSlot(), ScratchSlot())``.

        """
        super().__init__()
        is_overload_1 = isinstance(arg1, int) and arg2 is None
        is_overload_2 = isinstance(arg1, Expr) and isinstance(arg2, Expr)
        is_overload_3 = isinstance(arg1, ScratchSlot) and isinstance(arg2, ScratchSlot)
        correct_type = any([is_overload_1, is_overload_2, is_overload_3])

        if not correct_type:
            raise TealInputError(
                f"WideInt() requires `int` or `Expr, Expr`, got {arg1} of {type(arg1)} and {arg2} of {type(arg2)}"
            )

        if is_overload_1:

            arg1 = cast(int, arg1)
            wide_int = WideInt.FromInt(arg1)
        elif is_overload_2:
            arg1 = cast(Expr, arg1)
            arg2 = cast(Expr, arg2)
            wide_int = WideInt.FromExprExpr(arg1, arg2)
        else:
            arg1 = cast(ScratchSlot, arg1)
            arg2 = cast(ScratchSlot, arg2)
            self.hi = arg1
            self.lo = arg2
            # no store() needed
            return

        self.hi = wide_int.hi
        self.lo = wide_int.lo
        self.hi.store(self._hi_expr)
        self.lo.store(self._lo_expr)

    def __str__(self):
        return "(wide_int hi:{} lo:{})".format(self.hi, self.lo)

    def __teal__(self, options: "CompileOptions"):
        store_lo = self.lo.store(self._lo_expr).__teal__(options)
        store_hi = self.hi.store(self._hi_expr).__teal__(options)

        start = store_lo[0]
        end = store_lo[1]
        end.setNextBlock(store_hi[0])
        end = store_hi[1]

        return start, end

    def type_of(self):
        return TealType.none

    @property
    def high(self):
        return self.hi

    @property
    def low(self):
        return self.lo


WideInt.__module__ = "pyteal"
