from typing import Union, cast, TYPE_CHECKING

from ..types import TealType, require_type
from ..ir import TealOp, Op, TealBlock
from ..errors import TealInputError, verifyTealVersion
from .expr import Expr
from .leafexpr import LeafExpr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class Arg(LeafExpr):
    """An expression to get an argument when running in signature verification mode."""

    def __init__(self, index: Union[int, Expr]) -> None:
        """Get an argument for this program.

        Should only be used in signature verification mode. For application mode arguments, see
        :any:`TxnObject.application_args`.

        Args:
            index: The index of the argument to get. The index must be between 0 and 255 inclusive.
                Starting in TEAL v5, the index may be a PyTeal expression that evaluates to uint64.
        """
        super().__init__()

        if type(index) is int:
            if index < 0 or index > 255:
                raise TealInputError("invalid arg index {}".format(index))
        else:
            require_type(cast(Expr, index).type_of(), TealType.uint64)

        self.index = index

    def __teal__(self, options: "CompileOptions"):
        if type(self.index) is int:
            op = TealOp(self, Op.arg, self.index)
            return TealBlock.FromOp(options, op)

        verifyTealVersion(
            Op.args.min_version,
            options.version,
            "TEAL version too low to use dynamic indexes with Arg",
        )

        op = TealOp(self, Op.args)
        return TealBlock.FromOp(options, op, cast(Expr, self.index))

    def __str__(self):
        return "(arg {})".format(self.index)

    def type_of(self):
        return TealType.bytes


Arg.__module__ = "pyteal"
