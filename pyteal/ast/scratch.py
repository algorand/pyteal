from typing import TYPE_CHECKING

from ..types import TealType
from ..config import NUM_SLOTS
from ..errors import TealInputError
from .expr import Expr

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class ScratchSlot:
    """Represents the allocation of a scratch space slot."""

    # Unique identifier for the compiler to automatically assign slots
    # The id field is used by the compiler to map to an actual slot in the source code
    # Slot ids under 256 are manually reserved slots
    nextSlotId = NUM_SLOTS

    def __init__(self, requestedSlotId: int = None):
        """Initializes a scratch slot with a particular id

        Args:
            requestedSlotId (optional): A scratch slot id that the compiler must store the value.
            This id may be a Python int in the range [0-256).
        """
        if requestedSlotId is None:
            self.id = ScratchSlot.nextSlotId
            ScratchSlot.nextSlotId += 1
            self.isReservedSlot = False
        else:
            if requestedSlotId < 0 or requestedSlotId >= NUM_SLOTS:
                raise TealInputError(
                    "Invalid slot ID {}, shoud be in [0, {})".format(
                        requestedSlotId, NUM_SLOTS
                    )
                )
            self.id = requestedSlotId
            self.isReservedSlot = True

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

    def load(self, type: TealType = TealType.anytype) -> "ScratchLoad":
        """Get an expression to load a value from this slot.

        Args:
            type (optional): The type being loaded from this slot, if known. Defaults to
                TealType.anytype.
        """
        return ScratchLoad(self, type)

    def __repr__(self):
        return "ScratchSlot({})".format(self.id)

    def __str__(self):
        return "slot#{}".format(self.id)

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

    def __teal__(self, options: "CompileOptions"):
        from ..ir import TealOp, Op, TealBlock

        op = TealOp(self, Op.load, self.slot)
        return TealBlock.FromOp(options, op)

    def type_of(self):
        return self.type

    def has_return(self):
        return False


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

    def __teal__(self, options: "CompileOptions"):
        from ..ir import TealOp, Op, TealBlock

        op = TealOp(self, Op.store, self.slot)
        return TealBlock.FromOp(options, op, self.value)

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


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

    def __teal__(self, options: "CompileOptions"):
        from ..ir import TealOp, Op, TealBlock

        op = TealOp(self, Op.store, self.slot)
        return TealBlock.FromOp(options, op)

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


ScratchStackStore.__module__ = "pyteal"
