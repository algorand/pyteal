from abc import ABCMeta, abstractmethod
from typing import Callable, List, Tuple, TYPE_CHECKING

from pyteal.types import TealType, require_type
from pyteal.errors import TealInternalError, TealCompileError, TealInputError
from pyteal.ir import TealOp, Op, TealSimpleBlock, TealBlock, TealConditionalBlock
from pyteal.ast.expr import Expr
from pyteal.ast.leafexpr import LeafExpr
from pyteal.ast.scratch import ScratchSlot

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


def addU128U64(
    expr: Expr, term: Expr, options: "CompileOptions"
) -> Tuple[TealBlock, TealSimpleBlock]:
    termSrt, termEnd = term.__teal__(options)
    # stack is [..., A, B, C], where C is current term
    # need to pop all A, B, C from stack and push X, Y, where X and Y are:
    #      X * 2 ** 64 + Y = (A * 2 ** 64) + (B + C)
    # <=>  X * 2 ** 64 + Y = (A + highword(B + C)) * 2 ** 64 + lowword(B + C)
    # <=>  X = A + highword(B + C)
    #      Y = lowword(B + C)
    addition = TealSimpleBlock(
        [
            # stack: [..., A, highword(B + C), lowword(B + C)]
            TealOp(expr, Op.addw),
            # stack: [..., lowword(B + C), A, highword(B + C)]
            TealOp(expr, Op.cover, 2),
            # stack: [..., lowword(B + C), A + highword(B + C)]
            TealOp(expr, Op.add),
            # stack: [..., A + highword(B + C), lowword(B + C)]
            TealOp(expr, Op.uncover, 1),
        ]
    )
    termEnd.setNextBlock(addition)
    return termSrt, addition


def addTerms(
    expr: Expr, terms: List[Expr], options: "CompileOptions"
) -> Tuple[TealSimpleBlock, TealSimpleBlock]:
    if len(terms) == 0:
        raise TealInternalError("Received 0 terms")

    for term in terms:
        require_type(term, TealType.uint64)

    start = TealSimpleBlock([])

    term0srt, term0end = terms[0].__teal__(options)

    if len(terms) == 1:
        highword = TealSimpleBlock([TealOp(expr, Op.int, 0)])

        start.setNextBlock(highword)
        highword.setNextBlock(term0srt)
        end = term0end
    else:
        start.setNextBlock(term0srt)

        term1srt, term1end = terms[1].__teal__(options)
        term0end.setNextBlock(term1srt)
        addFirst2 = TealSimpleBlock([TealOp(expr, Op.addw)])
        term1end.setNextBlock(addFirst2)
        end = addFirst2

        for term in terms[2:]:
            termSrt, added = addU128U64(expr, term, options)
            end.setNextBlock(termSrt)
            end = added

    return start, end


def addU128(
    expr: Expr, term: Expr, options: "CompileOptions"
) -> Tuple[TealSimpleBlock, TealSimpleBlock]:
    start = TealSimpleBlock([])
    termSrt, termEnd = term.__teal__(options)
    # stack: [..., A, B, C, D]
    addition = TealSimpleBlock(
        [
            # stack: [..., A, C, D, B]
            TealOp(expr, Op.uncover, 2),
            # stack: [..., A, C, highword(B + D), lowword(B + D)]
            TealOp(expr, Op.addw),
            # stack: [..., lowword(B + D), A, C, highword(B + D)]
            TealOp(expr, Op.cover, 3),
            # stack: [..., lowword(B + D), highword(B + D), A, C]
            TealOp(expr, Op.cover, 2),
            # stack: [..., lowword(B + D), highword(B + D), A + C]
            TealOp(expr, Op.add),
            # stack: [..., lowword(B + D), highword(B + D) + A + C]
            TealOp(expr, Op.add),
            # stack: [..., highword(B + D) + A + C, lowword(B + D)]
            TealOp(expr, Op.swap),
        ]
    )
    start.setNextBlock(termSrt)
    termEnd.setNextBlock(addition)
    return start, addition


def __substrctU128U64(expr: Expr) -> Tuple[TealSimpleBlock, TealSimpleBlock]:
    # stack: [..., A, B, C], where A * 2 ** 64 + B is 128 bit uint, C is uint64
    substractPrep = TealSimpleBlock(
        [
            # stack: [..., A, B, C, B, C]
            TealOp(expr, Op.dup2),
            # stack: [..., A, B, C, B >= C]
            TealOp(expr, Op.gt),
        ]
    )
    substractCond = TealConditionalBlock([])
    substractTrueBlock = TealSimpleBlock(
        [
            # stack: [..., A, B - C]
            TealOp(expr, Op.minus)
        ]
    )

    substractFalseBlock = TealSimpleBlock(
        [
            # stack: [..., B, C, A]
            TealOp(expr, Op.uncover, 2),
            # stack: [..., B, C, A, A]
            TealOp(expr, Op.dup),
            # stack: [..., B, C, A, A, 1]
            TealOp(expr, Op.int, 1),
            # stack: [..., B, C, A, A >= 1],
            TealOp(expr, Op.gt),
            # stack: [..., B, C, A]
            TealOp(expr, Op.assert_),
            # stack: [..., B, C, A, 1]
            TealOp(expr, Op.int, 1),
            # stack: [..., B, C, A - 1]
            TealOp(expr, Op.minus),
            # stack: [..., A - 1, B, C]
            TealOp(expr, Op.cover, 2),
            # stack: [..., A - 1, C, B]
            TealOp(expr, Op.cover, 1),
            # stack: [..., A - 1, C - B]
            TealOp(expr, Op.minus),
            # stack: [..., A - 1, 2^64 - 1 - (C - B)]
            TealOp(expr, Op.bitwise_not),
            # stack: [..., A - 1, 2^64 - 1 - (C - B), 1]
            TealOp(expr, Op.int, 1),
            # stack: [..., A - 1, 2^64 - (C - B)]
            TealOp(expr, Op.add),
        ]
    )
    substractPrep.setNextBlock(substractCond)
    substractCond.setTrueBlock(substractTrueBlock)
    substractCond.setFalseBlock(substractFalseBlock)

    end = TealSimpleBlock([])
    substractTrueBlock.setNextBlock(end)
    substractFalseBlock.setNextBlock(end)
    return substractPrep, end


def substractU128U64(
    expr: Expr, rhsTerm: Expr, options: "CompileOptions"
) -> Tuple[TealBlock, TealSimpleBlock]:
    termSrt, termEnd = rhsTerm.__teal__(options)
    subsSrt, subsEnd = __substrctU128U64(expr)
    termEnd.setNextBlock(subsSrt)
    return termSrt, subsEnd


def substractU128(
    expr: Expr, rhsTerm: Expr, options: "CompileOptions"
) -> Tuple[TealSimpleBlock, TealSimpleBlock]:
    start = TealSimpleBlock([])
    rhsSrt, rhsEnd = rhsTerm.__teal__(options)
    start.setNextBlock(rhsSrt)
    rhsEnd.setNextBlock(rhsSrt)
    # stack: [..., A, B, C, D]
    highwordPrep = TealSimpleBlock(
        [
            # stack: [..., B, C, D, A]
            TealOp(expr, Op.uncover, 3),
            # stack: [..., B, D, A, C]
            TealOp(expr, Op.uncover, 2),
            # stack: [..., B, D, A, C, A, C]
            TealOp(expr, Op.dup2),
            # stack: [..., B, D, A, C, A >= C]
            TealOp(expr, Op.gt),
            # stack: [..., B, D, A, C]
            TealOp(expr, Op.assert_),
            # stack: [..., B, D, A - C]
            TealOp(expr, Op.minus),
            # stack: [..., A - C, B, D]
            TealOp(expr, Op.cover, 2),
        ]
    )
    rhsEnd.setNextBlock(highwordPrep)
    subsSrt, subsEnd = __substrctU128U64(expr)
    highwordPrep.setNextBlock(subsSrt)
    return start, subsEnd


def __multU128U64(expr: Expr) -> Tuple[TealSimpleBlock, TealSimpleBlock]:
    srt = TealSimpleBlock([])
    # stack: [..., A, B, C]
    multiply = TealSimpleBlock(
        [
            # stack: [..., B, C, A]
            TealOp(expr, Op.uncover, 2),
            # stack: [..., B, C, A, C]
            TealOp(expr, Op.dig, 1),
            # stack: [..., B, C, A*C]
            TealOp(expr, Op.mul),
            # stack: [..., A*C, B, C]
            TealOp(expr, Op.cover, 2),
            # stack: [..., A*C, highword(B*C), lowword(B*C)]
            TealOp(expr, Op.mulw),
            # stack: [..., lowword(B*C), A*C, highword(B*C)]
            TealOp(expr, Op.cover, 2),
            # stack: [..., lowword(B*C), A*C+highword(B*C)]
            TealOp(expr, Op.add),
            # stack: [..., A*C+highword(B*C), lowword(B*C)]
            TealOp(expr, Op.swap),
        ]
    )
    end = TealSimpleBlock([])
    srt.setNextBlock(multiply)
    multiply.setNextBlock(end)
    return srt, end


def multU128U64(
    expr: Expr, factor: Expr, options: "CompileOptions"
) -> Tuple[TealBlock, TealSimpleBlock]:
    facSrt, facEnd = factor.__teal__(options)
    # stack is [..., A, B, C], where C is current factor
    # need to pop all A,B,C from stack and push X,Y, where X and Y are:
    #       X * 2**64 + Y = (A * 2**64 + B) * C
    # <=>   X * 2**64 + Y = A * C * 2**64 + B * C
    # <=>   X = A * C + highword(B * C)
    #       Y = lowword(B * C)
    multSrt, multEnd = __multU128U64(expr)
    facEnd.setNextBlock(multSrt)
    return facSrt, multEnd


def multiplyFactors(
    expr: Expr, factors: List[Expr], options: "CompileOptions"
) -> Tuple[TealSimpleBlock, TealSimpleBlock]:
    if len(factors) == 0:
        raise TealInternalError("Received 0 factors")

    for factor in factors:
        require_type(factor, TealType.uint64)

    start = TealSimpleBlock([])

    fac0Start, fac0End = factors[0].__teal__(options)

    if len(factors) == 1:
        # need to use 0 as high word
        highword = TealSimpleBlock([TealOp(expr, Op.int, 0)])

        start.setNextBlock(highword)
        highword.setNextBlock(fac0Start)

        end = fac0End
    else:
        start.setNextBlock(fac0Start)

        fac1Start, fac1End = factors[1].__teal__(options)
        fac0End.setNextBlock(fac1Start)

        multiplyFirst2 = TealSimpleBlock([TealOp(expr, Op.mulw)])
        fac1End.setNextBlock(multiplyFirst2)

        end = multiplyFirst2
        for factor in factors[2:]:
            facSrt, multed = multU128U64(expr, factor, options)
            end.setNextBlock(facSrt)
            end = multed

    return start, end


def multU128(
    expr: Expr, rhsFactor: Expr, options: "CompileOptions"
) -> Tuple[TealSimpleBlock, TealSimpleBlock]:
    start = TealSimpleBlock([])
    rhsSrt, rhsEnd = rhsFactor.__teal__(options)
    start.setNextBlock(rhsSrt)
    # stack: [..., A, B, C, D]
    multPrep = TealSimpleBlock(
        [
            # stack; [..., B, C, D, A]
            TealOp(expr, Op.uncover, 3),
            # stack: [..., B, D, A, C]
            TealOp(expr, Op.uncover, 2),
            # stack: [..., B, D, A, C, A, C]
            TealOp(expr, Op.dup2),
            # stack: [..., B, D, A, C, A * C], if mul overflow, then u128 mult will also overflow
            TealOp(expr, Op.mul),
            # stack: [..., B, D, A, C, A * C != 0]
            TealOp(expr, Op.logic_not),
            # stack: [..., B, D, A, C], at least one of A and C is 0
            TealOp(expr, Op.assert_),
            # stack: [..., B, D, A, C, C]
            TealOp(expr, Op.dup),
            # stack: [..., B, D, C, C, A]
            TealOp(expr, Op.uncover, 2),
            # stack: [..., B, D, C, C + A]
            TealOp(expr, Op.add),
            # stack: [..., B, D, C, C + A, C + A]
            TealOp(expr, Op.dup),
            # stack: [..., B, D, C + A, C, C + A]
            TealOp(expr, Op.cover, 2),
            # stack: [..., B, D, C + A, C == C + A] decide C + A should be swapped to before B or D
            TealOp(expr, Op.eq),
        ]
    )
    rhsEnd.setNextBlock(multPrep)

    multCond = TealConditionalBlock([])
    multPrep.setNextBlock(multCond)

    # stack: [..., B, D, C]
    multCondTrue = TealSimpleBlock(
        [
            # stack: [..., B, C, D]
            TealOp(expr, Op.swap),
            # stack: [..., D, B, C]
            TealOp(expr, Op.cover, 2),
            # stack: [..., C, D, B]
            TealOp(expr, Op.cover, 2),
        ]
    )
    # stack: [..., B, D, A]
    multCondFalse = TealSimpleBlock(
        [
            # stack: [..., A, B, D]
            TealOp(expr, Op.cover, 2)
        ]
    )
    multCond.setTrueBlock(multCondTrue)
    multCond.setFalseBlock(multCondFalse)

    # stack: [..., C, D, B] or [..., A, B, D]
    multSrt, multEnd = __multU128U64(expr)
    multCondTrue.setNextBlock(multSrt)
    multCondFalse.setNextBlock(multSrt)

    return start, multEnd


class WideRatio(Expr):
    """A class used to calculate expressions of the form :code:`(N_1 * N_2 * N_3 * ...) / (D_1 * D_2 * D_3 * ...)`

    Use this class if all inputs to the expression are uint64s, the output fits in a uint64, and all
    intermediate values fit in a uint128.
    """

    def __init__(
        self, numeratorFactors: List[Expr], denominatorFactors: List[Expr]
    ) -> None:
        """Create a new WideRatio expression with the given numerator and denominator factors.

        This will calculate :code:`(N_1 * N_2 * N_3 * ...) / (D_1 * D_2 * D_3 * ...)`, where each
        :code:`N_i` represents an element in :code:`numeratorFactors` and each :code:`D_i`
        represents an element in :code:`denominatorFactors`.

        Requires program version 5 or higher.

        Args:
            numeratorFactors: The factors in the numerator of the ratio. This list must have at
                least 1 element. If this list has exactly 1 element, then denominatorFactors must
                have more than 1 element (otherwise basic division should be used).
            denominatorFactors: The factors in the denominator of the ratio. This list must have at
                least 1 element.
        """
        super().__init__()
        if len(numeratorFactors) == 0 or len(denominatorFactors) == 0:
            raise TealInternalError(
                "At least 1 factor must be present in the numerator and denominator"
            )
        if len(numeratorFactors) == 1 and len(denominatorFactors) == 1:
            raise TealInternalError(
                "There is only a single factor in the numerator and denominator. Use basic division instead."
            )
        self.numeratorFactors = numeratorFactors
        self.denominatorFactors = denominatorFactors

    def __teal__(self, options: "CompileOptions"):
        if options.version < Op.cover.min_version:
            raise TealCompileError(
                "WideRatio requires program version {} or higher".format(
                    Op.cover.min_version
                ),
                self,
            )

        numStart, numEnd = multiplyFactors(self, self.numeratorFactors, options)
        denomStart, denomEnd = multiplyFactors(self, self.denominatorFactors, options)
        numEnd.setNextBlock(denomStart)

        combine = TealSimpleBlock(
            [
                TealOp(self, Op.divmodw),
                TealOp(self, Op.pop),  # pop remainder low word
                TealOp(self, Op.pop),  # pop remainder high word
                TealOp(self, Op.swap),  # swap quotient high and low words
                TealOp(self, Op.logic_not),
                TealOp(self, Op.assert_),  # assert quotient high word is 0
                # end with quotient low word remaining on the stack
            ]
        )
        denomEnd.setNextBlock(combine)

        return numStart, combine

    def __str__(self):
        ret_str = "(WideRatio (*"
        for f in self.numeratorFactors:
            ret_str += " " + str(f)
        ret_str += ") (*"
        for f in self.denominatorFactors:
            ret_str += " " + str(f)
        ret_str += ")"
        return ret_str

    def type_of(self):
        return TealType.uint64

    def has_return(self):
        return False


WideRatio.__module__ = "pyteal"


class WideUint128(LeafExpr, metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, outputNum: int):
        super().__init__()
        if outputNum <= 0:
            raise TealInputError("number of output slot should be positive")
        self.output_slots = [ScratchSlot() for _ in range(outputNum)]

    def __add__(self, other: Expr):
        if isinstance(other, WideUint128):
            return self.addU128(other)
        else:
            require_type(other, TealType.uint64)
            return self.addU64(other)

    def addU128(self, other: "WideUint128"):
        if not isinstance(other, WideUint128) or len(other.output_slots) != 2:
            raise TealInputError("expected WideUint128 input for addU128")

        class WideUint128AddU128(WideUint128):
            def __init__(self, lhs: WideUint128, arg: WideUint128):
                WideUint128.__init__(self, 2)
                self.term = arg
                self.lhs = lhs

            def __teal__(self, options: "CompileOptions"):
                lhsSrt, lhsEnd = self.lhs.__teal__(options)
                addSrt, addEnd = addU128(self, self.term, options)
                lhsEnd.setNextBlock(addSrt)
                return lhsSrt, addEnd

            def __str__(self) -> str:
                return "(addW {} {})".format(self.lhs, self.term)

        return WideUint128AddU128(self, other)

    def addU64(self, other: Expr):
        require_type(other, TealType.uint64)

        class WideUint128AddU64(WideUint128):
            def __init__(self, lhs: WideUint128, arg: Expr):
                WideUint128.__init__(self, 2)
                self.term = arg
                self.lhs = lhs

            def __teal__(self, options: "CompileOptions"):
                lhsSrt, lhsEnd = self.lhs.__teal__(options)
                addSrt, addEnd = addU128U64(self, self.term, options)
                lhsEnd.setNextBlock(addSrt)
                return lhsSrt, addEnd

            def __str__(self) -> str:
                return "(addW {} {})".format(self.lhs, self.term)

        return WideUint128AddU64(self, other)

    def __sub__(self, other: Expr):
        if isinstance(other, WideUint128):
            return self.minusU128(other)
        else:
            require_type(other, TealType.uint64)
            return self.minusU64(other)

    def minusU128(self, other: "WideUint128"):
        if not isinstance(other, WideUint128) or len(other.output_slots) != 2:
            raise TealInputError("expected WideUint128 input for minusU128")

        class WideUint128MinusU128(WideUint128):
            def __init__(self, lhs: WideUint128, arg: WideUint128):
                WideUint128.__init__(self, 2)
                self.term = arg
                self.lhs = lhs

            def __teal__(self, options: "CompileOptions"):
                lhsSrt, lhsEnd = self.lhs.__teal__(options)
                subSrt, subEnd = substractU128(self, self.term, options)
                lhsEnd.setNextBlock(subSrt)
                return lhsSrt, subEnd

            def __str__(self) -> str:
                return "(minusW {} {})".format(self.lhs, self.term)

        return WideUint128MinusU128(self, other)

    def minusU64(self, other: Expr):
        require_type(other, TealType.uint64)

        class WideUint128MinusU64(WideUint128):
            def __init__(self, lhs: WideUint128, arg: Expr):
                WideUint128.__init__(self, 2)
                self.term = arg
                self.lhs = lhs

            def __teal__(self, options: "CompileOptions"):
                lhsSrt, lhsEnd = self.lhs.__teal__(options)
                subSrt, subEnd = substractU128U64(self, self.term, options)
                lhsEnd.setNextBlock(subSrt)
                return lhsSrt, subEnd

            def __str__(self) -> str:
                return "(minusW {} {})".format(self.lhs, self.term)

        return WideUint128MinusU64(self, other)

    def __mul__(self, other: Expr):
        if isinstance(other, WideUint128):
            return self.mulU128(other)
        else:
            require_type(other, TealType.uint64)
            return self.mulU64(other)

    def mulU128(self, other: "WideUint128"):
        if not isinstance(other, WideUint128) or len(other.output_slots) != 2:
            raise TealInputError("expected WideUint128 input for mulU128")

        class WideUint128MulU128(WideUint128):
            def __init__(self, lhs: WideUint128, arg: WideUint128):
                WideUint128.__init__(self, 2)
                self.term = arg
                self.lhs = lhs

            def __teal__(self, options: "CompileOptions"):
                lhsSrt, lhsEnd = self.lhs.__teal__(options)
                mulSrt, mulEnd = multU128(self, self.term, options)
                lhsEnd.setNextBlock(mulSrt)
                return lhsSrt, mulEnd

            def __str__(self) -> str:
                return "(mulW {} {})".format(self.lhs, self.term)

        return WideUint128MulU128(self, other)

    def mulU64(self, other: Expr):
        require_type(other, TealType.uint64)

        class WideUint128MulU64(WideUint128):
            def __init__(self, lhs: WideUint128, arg: Expr):
                WideUint128.__init__(self, 2)
                self.term = arg
                self.lhs = lhs

            def __teal__(self, options: "CompileOptions"):
                lhsSrt, lhsEnd = self.lhs.__teal__(options)
                mulSrt, mulEnd = multU128U64(self, self.term, options)
                lhsEnd.setNextBlock(mulSrt)
                return lhsSrt, mulEnd

            def __str__(self) -> str:
                return "(mulW {} {})".format(self.lhs, self.term)

        return WideUint128MulU64(self, other)

    def __truediv__(self, other: Expr):
        if isinstance(other, WideUint128):
            return self.divU128(other)
        else:
            require_type(other, TealType.uint64)
            return self.divU64(other)

    def divU128(self, other: "WideUint128"):
        if not isinstance(other, WideUint128) or len(other.output_slots) != 2:
            raise TealInputError("expected WideUint128 input for divU128")

        class WideUint128DivU128(WideUint128):
            def __init__(self, lhs: WideUint128, arg: WideUint128):
                WideUint128.__init__(self, 2)
                self.term = arg
                self.lhs = lhs

            def __teal__(self, options: "CompileOptions"):
                lhsSrt, lhsEnd = self.lhs.__teal__(options)
                termSrt, termEnd = self.term.__teal__(options)
                lhsEnd.setNextBlock(termSrt)
                divFromDivmodW = TealSimpleBlock(
                    [
                        TealOp(self, Op.divmodw),
                        TealOp(self, Op.pop),
                        TealOp(self, Op.pop),
                    ]
                )
                termEnd.setNextBlock(divFromDivmodW)
                return lhsSrt, divFromDivmodW

            def __str__(self) -> str:
                return "(divW {} {})".format(self.lhs, self.term)

        return WideUint128DivU128(self, other)

    def divU64(self, other: Expr):
        require_type(other, TealType.uint64)

        class WideUint128DivU64(WideUint128):
            def __init__(self, lhs: WideUint128, arg: Expr):
                WideUint128.__init__(self, 1)
                self.term = arg
                self.lhs = lhs

            def __teal__(self, options: "CompileOptions"):
                lhsSrt, lhsEnd = self.lhs.__teal__(options)
                termSrt, termEnd = self.term.__teal__(options)
                lhsEnd.setNextBlock(termSrt)
                divFromDivW = TealSimpleBlock(
                    [
                        TealOp(self, Op.divw),
                    ]
                )
                termEnd.setNextBlock(divFromDivW)
                return lhsSrt, divFromDivW

            def __str__(self) -> str:
                return "(divW {} {})".format(self.lhs, self.term)

        return WideUint128DivU64(self, other)

    def __mod__(self, other: Expr):
        if isinstance(other, WideUint128):
            return self.modU128(other)
        else:
            require_type(other, TealType.uint64)
            return self.modU64(other)

    def modU128(self, other: "WideUint128"):
        if not isinstance(other, WideUint128) or len(other.output_slots) != 2:
            raise TealInputError("expected WideUint128 input for modU128")

        class WideUint128ModU128(WideUint128):
            def __init__(self, lhs: WideUint128, arg: WideUint128):
                WideUint128.__init__(self, 2)
                self.term = arg
                self.lhs = lhs

            def __teal__(self, options: "CompileOptions"):
                lhsSrt, lhsEnd = self.lhs.__teal__(options)
                termSrt, termEnd = self.term.__teal__(options)
                lhsEnd.setNextBlock(termSrt)
                modFromDivModW = TealSimpleBlock(
                    [
                        # stack: [..., divH, divL, modH, modL]
                        TealOp(self, Op.divmodw),
                        # stack: [..., divL, modH, modL, divH]
                        TealOp(self, Op.uncover, 3),
                        # stack: [..., modH, modL, divH, divL]
                        TealOp(self, Op.uncover, 3),
                        TealOp(self, Op.pop),
                        TealOp(self, Op.pop),
                    ]
                )
                termEnd.setNextBlock(modFromDivModW)
                return lhsSrt, modFromDivModW

            def __str__(self) -> str:
                return "(modW {} {})".format(self.lhs, self.term)

        return WideUint128ModU128(self, other)

    def modU64(self, other: Expr):
        require_type(other, TealType.uint64)

        class WideUint128ModU64(WideUint128):
            def __init__(self, lhs: WideUint128, arg: Expr):
                WideUint128.__init__(self, 2)
                self.term = arg
                self.lhs = lhs

            def __teal__(self, options: "CompileOptions"):
                lhsSrt, lhsEnd = self.lhs.__teal__(options)
                termSrt, termEnd = self.term.__teal__(options)
                lhsEnd.setNextBlock(termSrt)
                divFromDivW = TealSimpleBlock(
                    [
                        # stack: [..., A, B, C, 0]
                        TealOp(self, Op.int, 0),
                        # stack: [..., A, B, 0, C]
                        TealOp(self, Op.swap),
                        # stack: [..., divH, divL, modH, modL]
                        TealOp(self, Op.divmodw),
                        # stack: [..., divL, modH, modL, divH]
                        TealOp(self, Op.uncover, 3),
                        # stack: [..., modH, modL, divH, divL]
                        TealOp(self, Op.uncover, 3),
                        # stack: [..., modH, modL, divH]
                        TealOp(self, Op.pop),
                        # stack: [..., modH, modL]
                        TealOp(self, Op.pop),
                        # stack: [..., modL, modH]
                        TealOp(self, Op.swap),
                        # stack: [..., modL]
                        TealOp(self, Op.pop),
                    ]
                )
                termEnd.setNextBlock(divFromDivW)
                return lhsSrt, divFromDivW

            def __str__(self) -> str:
                return "(modW {} {})".format(self.lhs, self.term)

        return WideUint128ModU64(self, other).toUint64()

    def __divmod__(self, other: "WideUint128"):
        if not isinstance(other, WideUint128) or len(other.output_slots) != 2:
            raise TealInputError("expected WideUint128 input for divmodW")

        class WideUint128DivmodW(WideUint128):
            def __init__(self, lhs: WideUint128, rhs: WideUint128):
                WideUint128.__init__(self, 4)
                self.lhs = lhs
                self.term = rhs

            def __teal__(
                self, options: "CompileOptions"
            ) -> Tuple[TealBlock, TealSimpleBlock]:
                lhsSrt, lhsEnd = self.lhs.__teal__(options)
                termSrt, termEnd = self.term.__teal__(options)
                lhsEnd.setNextBlock(termSrt)
                divmodW = TealSimpleBlock([TealOp(self, Op.divmodw)])
                termEnd.setNextBlock(divmodW)
                return lhsSrt, divmodW

            def __str__(self) -> str:
                return "(divmodW {} {})".format(self.lhs, self.term)

        return WideUint128DivmodW(self, other)

    def type_of(self) -> TealType:
        return TealType.uint64 if len(self.output_slots) == 1 else TealType.none

    def toUint64(self) -> Expr:
        if self.type_of() == TealType.uint64:
            raise TealInternalError("expression is already evaluated to uint64")
        elif len(self.output_slots) > 2:
            raise TealInternalError("expression is only appliable for uint128")

        class WideUint128ToUint64(Expr):
            def __init__(self, wideArith: WideUint128):
                super().__init__()
                self.wideArith = wideArith

            def type_of(self) -> TealType:
                return TealType.uint64

            def has_return(self) -> bool:
                return False

            def __teal__(
                self, options: "CompileOptions"
            ) -> Tuple[TealBlock, TealSimpleBlock]:
                arithSrt, arithEnd = self.wideArith.__teal__(options)
                reducer = TealSimpleBlock(
                    [
                        TealOp(self, Op.swap),
                        TealOp(self, Op.logic_not),
                        TealOp(self, Op.assert_),
                    ]
                )
                arithEnd.setNextBlock(reducer)
                return arithSrt, reducer

            def __str__(self) -> str:
                return "(toUint64 {})".format(self.wideArith)

        return WideUint128ToUint64(self)

    def toBinary(self) -> Expr:
        if self.type_of() == TealType.uint64:
            raise TealInternalError("expression is already evaluated to uint64")
        elif len(self.output_slots) > 2:
            raise TealInternalError("expression is only appliable for uint128")

        class WideUint128ToBinary(Expr):
            def __init__(self, wideArith: WideUint128):
                super().__init__()
                self.wideArith = wideArith

            def type_of(self) -> TealType:
                return TealType.bytes

            def has_return(self) -> bool:
                return False

            def __teal__(
                self, options: "CompileOptions"
            ) -> Tuple[TealBlock, TealSimpleBlock]:
                arithSrt, arithEnd = self.wideArith.__teal__(options)
                reducer = TealSimpleBlock(
                    [
                        TealOp(self, Op.itob),
                        TealOp(self, Op.swap),
                        TealOp(self, Op.itob),
                        TealOp(self, Op.swap),
                        TealOp(self, Op.concat),
                    ]
                )
                arithEnd.setNextBlock(reducer)
                return arithSrt, reducer

            def __str__(self) -> str:
                return "(toBinary {})".format(self.wideArith)

        return WideUint128ToBinary(self)

    def reduceTo(self, reducer: Callable[..., Expr]):
        if self.type_of() == TealType.uint64:
            raise TealInternalError("expression is already evaluated to uint64")

        class WideUint128Reduced(Expr):
            def __init__(self, wideArith: WideUint128):
                super().__init__()
                self.wideArith = wideArith

                argsLoaded = [
                    slot.load(TealType.uint64) for slot in self.wideArith.output_slots
                ]
                self.reduceExpr = reducer(argsLoaded)

            def __str__(self) -> str:
                return "(reduced {})".format(self.wideArith)

            def __teal__(
                self, options: "CompileOptions"
            ) -> Tuple[TealBlock, TealSimpleBlock]:
                srt = TealSimpleBlock([])
                curEnd = srt
                for slot in reversed(self.wideArith.output_slots):
                    store = slot.store()
                    storeSrt, storeEnd = store.__teal__(options)
                    curEnd.setNextBlock(storeSrt)
                    curEnd = storeEnd
                reduceSrt, reduceEnd = self.reduceExpr.__teal__(options)
                curEnd.setNextBlock(reduceSrt)
                return srt, reduceEnd

            def type_of(self) -> TealType:
                return self.reduceExpr.type_of()

            def has_return(self) -> bool:
                return False

        return WideUint128Reduced(self)


WideUint128.__module__ = "pyteal"

# (A + B - C) * D
# sumW(A, B).minus(C).mul(D).reduce(lambda high, low: Seq(Assert(Not(high)), low)) # alias as .to64Bits()
# sumW(A, B).minus(C).mul(D).reduce(lambda high, low: Concat(Itob(high), Itob(low))) # alias as .toBinary()

# (A + B) - (C * D)
# sumW(A, B).minus(mulW(C, D)).toUint64()
# (sumW(A, B) - prodW(C, D)).toUint64()


def sumW(*terms: Expr):
    if len(terms) < 2:
        raise TealInternalError("received term number less than 2")

    for term in terms:
        require_type(term, TealType.uint64)

    class WideUint128Sum(WideUint128):
        def __init__(self, *args: Expr):
            WideUint128.__init__(self, 2)
            self.terms = list(args)

        def __teal__(self, options: "CompileOptions"):
            return addTerms(self, self.terms, options)

        def __str__(self) -> str:
            return "(addw {})".format(" ".join([t.__str__() for t in self.terms]))

    return WideUint128Sum(*terms)


def prodW(*factors: Expr):
    if len(factors) < 2:
        raise TealInternalError("received factor number less than 2")

    for factor in factors:
        require_type(factor, TealType.uint64)

    class WideUint128Prod(WideUint128):
        def __init__(self, *args: Expr):
            WideUint128.__init__(self, 2)
            self.factors = list(args)

        def __teal__(self, options: "CompileOptions"):
            return multiplyFactors(self, self.factors, options)

        def __str__(self) -> str:
            return "(mulw {})".format(" ".join([f.__str__() for f in self.factors]))

    return WideUint128Prod(*factors)


def expW(base: Expr, _pow: Expr):
    require_type(base, TealType.uint64)
    require_type(_pow, TealType.uint64)

    class WideUint128Exp(WideUint128):
        def __init__(self, *args: Expr):
            WideUint128.__init__(self, 2)
            self.base = args[0]
            self.power = args[1]

        def __teal__(self, options: "CompileOptions"):
            return TealBlock.FromOp(
                options, TealOp(self, Op.expw), self.base, self.power
            )

        def __str__(self) -> str:
            return "(expw {} {})".format(self.base.__str__(), self.power.__str__())

    return WideUint128Exp(base, _pow)
