from ..types import TealType, require_type
from .expr import Expr
from .scratch import ScratchSlot, ScratchLoad


class ScratchVar:
    """
    Interface around Scratch space, similiar to get/put local/global state

    Example:
        .. code-block:: python

            myvar = ScratchVar(TealType.uint64)
            Seq([
                myvar.store(Int(5)),
                Assert(myvar.load() == Int(5))
            ])
    """

    MAX_STACK_DEPTH = 700 * 256 / 2

    def __init__(
        self,
        type: TealType = TealType.anytype,
        slotId: int = None,
        *,
        slodIdFromStack: bool = False,
    ):
        """Create a new ScratchVar with an optional type.

        Args:
            type (optional): The type that this variable can hold. An error will be thrown if an
                expression with an incompatiable type is stored in this variable. Defaults to
                TealType.anytype.
            slotId (optional): A scratch slot id that the compiler must store the value.
                This id may be a Python int in the range [0-256).
        """
        assert (
            slotId is None or not slodIdFromStack
        ), "cannot specify explicit slotId when fromStack"

        self.slotIdFromStack = slodIdFromStack

        # when slotIdFromStack is True, slotId is therefore None and self.slot.store(Expr) will make sense
        self.slot = ScratchSlot(requestedSlotId=slotId)
        self.type = type

    def storage_type(self) -> TealType:
        """Get the type of expressions that can be stored in this ScratchVar."""
        return self.type

    def store(self, value: Expr) -> Expr:
        """Store value in Scratch Space

        Args:
            value: The value to store. Must conform to this ScratchVar's type.
        """
        require_type(value, self.type)
        return self.slot.store(value)

    def load(self) -> ScratchLoad:
        """Load value from Scratch Space"""
        return self.slot.load(self.type)


ScratchVar.__module__ = "pyteal"
