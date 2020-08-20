from ..types import TealType
from ..ir import TealOp, Op
from ..errors import TealInputError
from .leafexpr import LeafExpr

class Arg(LeafExpr):
    """An expression to get an argument when running in signature verification mode."""

    def __init__(self, index: int) -> None:
        """Get an argument for this program.
        
        Should only be used in signature verification mode. For application mode arguments, see
        :any:`TxnObject.application_args`.

        Args:
            index: The integer index of the argument to get. Must be between 0 and 255 inclusive.
        """
        if type(index) is not int:
            raise TealInputError("invalid arg input type {}".format(type(index)))

        if index < 0 or index > 255:
            raise TealInputError("invalid arg index {}".format(index))

        self.index = index

    def __teal__(self):
        return [TealOp(Op.arg, self.index)]
        
    def __str__(self):
        return "(arg {})".format(self.index)

    def type_of(self):
        return TealType.bytes

Arg.__module__ = "pyteal"
