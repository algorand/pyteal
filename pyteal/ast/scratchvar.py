from operator import index
from typing import cast

from ..types import TealType, require_type
from .expr import Expr
from .int import Int
from .scratch import ScratchSlot, ScratchLoad, DynamicSlot


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

    Example of Dynamic Scratch space whereby the slot index is picked up from the stack:
        .. code-block:: python
                player_index = ScratchVar(TealType.uint64)
                player_score = ScratchVar(TealType.uint64, player_index.load())
                Seq(
                    player_index.store(Int(129)),     # Wilt Chamberlain
                    player_score.store(Int(100)),
                    player_index.store(Int(130)),     # Kobe Bryant
                    player_score.store(Int(81)),
                    player_index.store(Int(131)),     # David Thompson
                    player_score.store(Int(73)),
                    Assert(player_score.load() == Int(73)),
                    Assert(player_score.index() == Int(131)),
                    player_score.store(player_score.load() - Int(2)),     # back to Wilt:
                    Assert(player_score.load() == Int(100)),
                    Assert(player_score.index() == Int(129)),
                )
    """

    # TODO: In the case that a DYNAMIC scratch variable is detected, we should limit the auto-assigned slot indices to less than < 128
    # and suggest a best practice of requiring (without checking) that dynamic slot expressions should be in the range [128-255)

    def __init__(self, type: TealType = TealType.anytype, slotId: int = None):
        """Create a new ScratchVar with an optional type.

        Args:
            type (optional): The type that this variable can hold. An error will be thrown if an
                expression with an incompatiable type is stored in this variable. Defaults to
                TealType.anytype.
            slotId (optional): A scratch slot id that the compiler must store the value.
                This id may be a Python int in the range [0-256).
        """

        # TODO: Zeph to add assertions

        self.slot = (
            ScratchSlot(requestedSlotId=slotId)
            if not isinstance(slotId, Expr)
            else DynamicSlot(cast(Expr, slotId))
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

    def index(self) -> Expr:
        return self.slot.index()


ScratchVar.__module__ = "pyteal"


class PassByRefScratchVar(ScratchVar):
    def __init__(self, sv: ScratchVar):
        self.ref: ScratchVar = sv
        self.slot = self.ref.slot

    def store(self, value: Expr) -> Expr:
        dynsv = ScratchVar(TealType.uint64, self.ref.load())
        return dynsv.store(value)

    def load(self) -> ScratchLoad:
        dynsv = ScratchVar(TealType.uint64, self.ref.load())
        return dynsv.load()

    def index(self) -> Expr:
        return self.ref.index()


PassByRefScratchVar.__module__ = "pyteal"
