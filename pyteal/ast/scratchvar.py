from typing import Union

from ..types import require_type, TealType

from .expr import Expr
from .int import Int
from .scratch import DynamicSlot, ScratchSlot, ScratchLoad, Slot


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
    ):
        """Create a new ScratchVar with an optional type and slot index

        Args:
            type (optional): The type that this variable can hold. An error will be thrown if an
                expression with an incompatiable type is stored in this variable. Defaults to
                TealType.anytype.
            slotId (optional): A scratch slot id that the compiler must store the value.
                This id may be a Python int in the range [0-256).
        """

        assert slotId is None or isinstance(
            slotId, (int, Expr)
        ), "slotId of type {} is disallowed".format(type(slotId))

        self.slot: Slot = (
            DynamicSlot(slotId) if isinstance(slotId, Expr) else ScratchSlot(slotId)
        )

        self.type = type
        self._subroutineInternal = False

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

    # TODO: Can I get this to work?
    # def index(self) -> Expr:
    #     return self.slot.id if self.slot.dynamic() else Int(self.slot.id)


ScratchVar.__module__ = "pyteal"
