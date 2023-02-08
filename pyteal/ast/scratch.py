from typing import cast, TYPE_CHECKING

from pyteal.types import TealType, require_type
from pyteal.config import NUM_SLOTS
from pyteal.errors import TealInputError, TealInternalError
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class ScratchSlot:
    """Represents the allocation of a scratch space slot."""

    # Unique identifier for the compiler to automatically assign slots
    # The id field is used by the compiler to map to an actual slot in the source code
    # Slot ids under 256 are manually reserved slots
    nextSlotId: int = NUM_SLOTS

    @classmethod
    def reset_slot_numbering(cls, start_index: int = NUM_SLOTS) -> None:
        cls.nextSlotId = start_index

    def __init__(self, requestedSlotId: int | None = None):
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
                    "Invalid slot ID {}, should be in [0, {})".format(
                        requestedSlotId, NUM_SLOTS
                    )
                )
            self.id = requestedSlotId
            self.isReservedSlot = True

    def store(self, value: Expr | None = None) -> Expr:
        """Get an expression to store a value in this slot.

        Args:
            value (optional): The value to store in this slot.
                If not included, the last value on the stack will be stored.
                NOTE: storing the last value on the stack breaks the typical
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

    def index(self) -> "ScratchIndex":
        return ScratchIndex(self)

    def __repr__(self):
        return "ScratchSlot({})".format(self.id)

    def __str__(self):
        return "slot#{}".format(self.id)


ScratchSlot.__module__ = "pyteal"


class ScratchIndex(Expr):
    def __init__(self, slot: ScratchSlot):
        super().__init__()
        self.slot = slot

    def __str__(self):
        return "(ScratchIndex {})".format(self.slot)

    def type_of(self):
        return TealType.uint64

    def has_return(self):
        return False

    def __teal__(self, options: "CompileOptions"):
        from pyteal.ir import TealOp, Op, TealBlock

        op = TealOp(self, Op.int, self.slot)
        return TealBlock.FromOp(options, op)


ScratchIndex.__module__ = "pyteal"


class ScratchLoad(Expr):
    """Expression to load a value from scratch space."""

    def __init__(
        self,
        slot: ScratchSlot | None = None,
        type: TealType = TealType.anytype,
        index_expression: Expr | None = None,
    ):
        """Create a new ScratchLoad expression.

        Args:
            slot (optional): The slot to load the value from.
            type (optional): The type being loaded from this slot, if known. Defaults to
                TealType.anytype.
            index_expression (optional): As an alternative to slot,
                an expression can be supplied for the slot index.
        """
        super().__init__()

        if (slot is None) == (index_expression is None):
            raise TealInputError(
                "Exactly one of slot or index_expressions must be provided"
            )

        if index_expression:
            if not isinstance(index_expression, Expr):
                raise TealInputError(
                    "index_expression must be an Expr but was of type {}".format(
                        type(index_expression)
                    )
                )
            require_type(index_expression, TealType.uint64)

        if slot and not isinstance(slot, ScratchSlot):
            raise TealInputError(
                "cannot handle slot of type {}".format(type(self.slot))
            )

        self.slot = slot
        self.type = type
        self.index_expression = index_expression

    def __str__(self):
        return "(Load {})".format(self.slot if self.slot else self.index_expression)

    def __teal__(self, options: "CompileOptions"):
        from pyteal.ir import TealOp, Op, TealBlock

        if self.index_expression is not None:
            op = TealOp(self, Op.loads)
            return TealBlock.FromOp(options, op, self.index_expression)

        s = cast(ScratchSlot, self.slot)
        op = TealOp(self, Op.load, s)
        return TealBlock.FromOp(options, op)

    def type_of(self):
        return self.type

    def has_return(self):
        return False


ScratchLoad.__module__ = "pyteal"


class ScratchStore(Expr):
    """Expression to store a value in scratch space."""

    def __init__(
        self,
        slot: ScratchSlot | None,
        value: Expr,
        index_expression: Expr | None = None,
    ):
        """Create a new ScratchStore expression.

        Args:
            slot (optional): The slot to store the value in.
            value: The value to store.
            index_expression (optional): As an alternative to slot,
                an expression can be supplied for the slot index.
        """
        super().__init__()

        if (slot is None) == (index_expression is None):
            raise TealInternalError(
                "Exactly one of slot or index_expressions must be provided"
            )

        if index_expression:
            if not isinstance(index_expression, Expr):
                raise TealInputError(
                    "index_expression must be an Expr but was of type {}".format(
                        type(index_expression)
                    )
                )
            require_type(index_expression, TealType.uint64)

        self.slot = slot
        self.value = value
        self.index_expression = index_expression

    def __str__(self):
        return "(Store {} {})".format(
            self.slot if self.slot else self.index_expression, self.value
        )

    def __teal__(self, options: "CompileOptions"):
        from pyteal.ir import TealOp, Op, TealBlock

        if self.index_expression is not None:
            op = TealOp(self, Op.stores)
            return TealBlock.FromOp(options, op, self.index_expression, self.value)

        if not isinstance(self.slot, ScratchSlot):
            raise TealInternalError(
                "cannot handle slot of type {}".format(type(self.slot))
            )
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
        self._sframes_container: Expr | None = None

    def __str__(self):
        return "(StackStore {})".format(self.slot)

    def __teal__(self, options: "CompileOptions"):
        from pyteal.ir import TealOp, Op, TealBlock

        op = TealOp(self, Op.store, self.slot)
        op._sframes_container = self._sframes_container
        return TealBlock.FromOp(options, op)

    def type_of(self):
        return TealType.none

    def has_return(self):
        return False


ScratchStackStore.__module__ = "pyteal"
