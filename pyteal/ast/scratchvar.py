from typing import Union

from ..types import TealType, require_type
from .expr import Expr
from .scratch import ScratchSlot, ScratchLoad, Slot, DynamicSlot


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

    def __init__(
        self,
        type: TealType = TealType.anytype,
        slotId: Union[int, Expr] = None,
        forceSlotIdFromStack: bool = False,
    ):
        """Create a new ScratchVar with an optional type.
        TODO: fix this comment (Zeph)

        Args:
            type (optional): The type that this variable can hold. An error will be thrown if an
                expression with an incompatiable type is stored in this variable. Defaults to
                TealType.anytype.
            slotId (optional): A scratch slot id that the compiler must store the value.
                This id may be a Python int in the range [0-256).
        """
        # slotId:
        # None & not forceSlotIdFromStack -> (as before) Compiler defines implicit slotId using load/store
        # None & forceSlotIdFromStack -> (new and not recommended) slotId using loads/stores from whatever on top of stack
        # int  -> (as before) explicit user defined slotId using load/store
        # Expr -> (new) runtime defined slotId that is put on the stack right before accessing using loads/stores
        assert slotId is None or isinstance(
            slotId, (int, Expr)
        ), "slotId of type {} is disallowed".format(type(slotId))

        assert not forceSlotIdFromStack or not isinstance(
            slotId, int
        ), "cannot pick up slotId from when it is explicitly given ({})".format(slotId)

        # TODO: handle the case forceSlotIdFromStack (are we done?????)
        self.slotIdFromStack = forceSlotIdFromStack or isinstance(slotId, Expr)

        # TODO: when isinstance(slotId, Expr): do self.slot() will return something else
        self.slot: Slot = (
            DynamicSlot(slotId) if self.slotIdFromStack else ScratchSlot(slotId)
        )
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
