from typing import List, Tuple, TYPE_CHECKING

from ..types import TealType, require_type
from ..errors import TealInputError, TealInternalError, TealCompileError
from ..ir import TealOp, Op, TealSimpleBlock, TealBlock
from .expr import Expr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


def multiplyFactors(
    expr: Expr, factors: List[Expr], options: "CompileOptions"
) -> Tuple[TealSimpleBlock, TealSimpleBlock]:
    if len(factors) == 0:
        raise TealInternalError("Received 0 factors")

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
            facXStart, facXEnd = factor.__teal__(options)
            end.setNextBlock(facXStart)

            # stack is [..., A, B, C], where C is current factor
            # need to pop all A,B,C from stack and push X,Y, where X and Y are:
            #       X * 2**64 + Y = (A * 2**64 + B) * C
            # <=>   X * 2**64 + Y = A * C * 2**64 + B * C
            # <=>   X = A * C + highword(B * C)
            #       Y = lowword(B * C)
            multiply = TealSimpleBlock(
                [
                    TealOp(expr, Op.uncover, 2),  # stack: [..., B, C, A]
                    TealOp(expr, Op.dig, 1),  # stack: [..., B, C, A, C]
                    TealOp(expr, Op.mul),  # stack: [..., B, C, A*C]
                    TealOp(expr, Op.cover, 2),  # stack: [..., A*C, B, C]
                    TealOp(
                        expr, Op.mulw
                    ),  # stack: [..., A*C, highword(B*C), lowword(B*C)]
                    TealOp(
                        expr, Op.cover, 2
                    ),  # stack: [..., lowword(B*C), A*C, highword(B*C)]
                    TealOp(
                        expr, Op.add
                    ),  # stack: [..., lowword(B*C), A*C+highword(B*C)]
                    TealOp(
                        expr, Op.swap
                    ),  # stack: [..., A*C+highword(B*C), lowword(B*C)]
                ]
            )

            facXEnd.setNextBlock(multiply)
            end = multiply

    return start, end


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

        Requires TEAL version 5 or higher.

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
                "WideRatio requires TEAL version {} or higher".format(
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
