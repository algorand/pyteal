from ..types import TealType
from ..errors import TealInputError
from .leafexpr import LeafExpr

class Int(LeafExpr):
    """An expression that represents a uint64."""
     
    def __init__(self, value: int) -> None:
        """Create a new uint64.

        Args:
            value: The integer value this uint64 will represent. Must be a positive value less than
            2**64.
        """
        if type(value) is not int:
            raise TealInputError("invalid input type {} to Int".format(type(value))) 
        elif value >= 0 and value < 2 ** 64:
            self.value = value
        else:
            raise TealInputError("Int {} is out of range".format(value))

    def __teal__(self):
        return [["int", str(self.value)]]
       
    def __str__(self):
        return "(Int: {})".format(self.value)

    def type_of(self):
        return TealType.uint64
