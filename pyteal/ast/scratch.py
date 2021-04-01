from typing import TYPE_CHECKING

from ..types import TealType
from .expr import Expr

if TYPE_CHECKING:
    from ..compiler import CompileOptions

class ScratchSlot:
    """Represents the allocation of a scratch space slot."""

    slotId = 0

    def __init__(self):
        self.id = ScratchSlot.slotId
        ScratchSlot.slotId += 1

    def store(self, value: Expr = None) -> Expr:
        """Get an expression to store a value in this slot.
        
        Args:
            value (optional): The value to store in this slot. If not included, the last value on
            the stack will be stored. NOTE: storing the last value on the stack breaks the typical
            semantics of PyTeal, only use if you know what you're doing.
        """
        if value is not None:
            return ScratchStore(self, value)
        return ScratchStackStore(self)

    def load(self, type: TealType = TealType.anytype) -> 'ScratchLoad':
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
        super().__init__()
        self.slot = slot
        self.type = type

    def __str__(self):
        return "(Load {})".format(self.slot)

    def __teal__(self, options: 'CompileOptions'):
        from ..ir import TealOp, Op, TealBlock
        op = TealOp(self, Op.load, self.slot)
        return TealBlock.FromOp(options, op)

    def type_of(self):
        return self.type

ScratchLoad.__module__ = "pyteal"

class ScratchStore(Expr):
    """Expression to store a value in scratch space."""

    def __init__(self, slot: ScratchSlot, value: Expr):
        """Create a new ScratchStore expression.

        Args:
            slot: The slot to store the value in.
            value: The value to store.
        """
        super().__init__()
        self.slot = slot
        self.value = value

    def __str__(self):
        return "(Store {} {})".format(self.slot, self.value)

    def __teal__(self, options: 'CompileOptions'):
        from ..ir import TealOp, Op, TealBlock
        op = TealOp(self, Op.store, self.slot)
        return TealBlock.FromOp(options, op, self.value)

    def type_of(self):
        return TealType.none

ScratchStore.__module__ = "pyteal"

class ScratchStackStore(Expr):
    """Expression to store a value from the stack in scratch space.
    
    NOTE: This expression breaks the typical semantics of PyTeal, only use if you know what you're
    doing.
    """

    def __init__(self, slot: ScratchSlot):
        """Create a new ScratchStackStore expression.

        Args:
            slot: The slot to store the value in.
        """
        super().__init__()
        self.slot = slot

    def __str__(self):
        return "(StackStore {})".format(self.slot)

    def __teal__(self, options: 'CompileOptions'):
        from ..ir import TealOp, Op, TealBlock
        op = TealOp(self, Op.store, self.slot)
        return TealBlock.FromOp(options, op)

    def type_of(self):
        return TealType.none

ScratchStackStore.__module__ = "pyteal"
