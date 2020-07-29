from ..types import TealType
from ..errors import TealInputError
from .leafexpr import LeafExpr

class Arg(LeafExpr):
    """An expression to get an argument."""
    
    def __init__(self, index:int) -> None:
        """Get an argument for this program.
        
        Args:
            index: The integer index of the argument to get. Must be between 0 and 255 inclusive.
        """
        if type(index) is not int:
            raise TealInputError("invalid arg input type {}".format(type(index)))

        if index < 0 or index > 255:
            raise TealInputError("invalid arg index {}".format(index))

        self.index = index

    def __teal__(self):
        return [["arg", str(self.index)]]
        
    def __str__(self):
        return "(arg {})".format(self.index)

    def type_of(self):
        return TealType.bytes
