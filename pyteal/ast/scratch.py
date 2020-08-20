from ..types import TealType
from .expr import Expr

class ScratchSlot:
    """Represents the allocation of a scratch space slot."""

    slotId = 0

    def __init__(self):
        self.id = ScratchSlot.slotId
        ScratchSlot.slotId += 1

    def store(self):
        """Get an expression to store a value in this slot."""
        return ScratchStore(self)

    def load(self, type: TealType = TealType.anytype):
        """Get an expression to load a value from this slot.

        Args:
            type (optional): The type being loaded from this slot, if known. Defaults to
                TealType.anytype.
        """
        return ScratchLoad(self, type)
    
    def __str__(self):
        return "slot#{}".format(self.id)
    
    def __eq__(self, other):
        if isinstance(other, ScratchSlot):
            return self.id == other.id
        return False
    
    def __hash__(self):
        return hash(self.id)

ScratchSlot.__module__ = "pyteal"

class ScratchLoad(Expr):
    """Expression to load a value from scratch space."""

    def __init__(self, slot: ScratchSlot, type: TealType = TealType.anytype):
        """Create a new ScratchLoad expression.

        Args:
            slot: The slot to load the value from.
            type (optional): The type being loaded from this slot, if known. Defaults to
                TealType.anytype.
        """
        self.slot = slot
        self.type = type

    def __str__(self):
        return "(Load {})".format(self.slot.__str__())

    def __teal__(self):
        from ..ir import TealOp, Op
        return [TealOp(Op.load, self.slot)]

    def type_of(self):
        return self.type

ScratchLoad.__module__ = "pyteal"

class ScratchStore(Expr):
    """Expression to store a value in scratch space."""

    def __init__(self, slot: ScratchSlot):
        """Create a new ScratchStore expression.

        Args:
            slot: The slot to store the value in.
        """
        self.slot = slot

    def __str__(self):
        return "(Store {})".format(self.slot.__str__())

    def __teal__(self):
        from ..ir import TealOp, Op
        return [TealOp(Op.store, self.slot)]

    def type_of(self):
        return TealType.none

ScratchStore.__module__ = "pyteal"
