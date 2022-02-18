from operator import index
from typing import cast

from ..errors import TealInputError, TealInternalError
from ..types import TealType, require_type

from .expr import Expr
from .int import Int
from .scratch import ScratchSlot, ScratchLoad, ScratchStore


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

    def __init__(self, type: TealType = TealType.anytype, slotId: int = None):
        """Create a new ScratchVar with an optional type.

        Args:
            type (optional): The type that this variable can hold. An error will be thrown if an
                expression with an incompatiable type is stored in this variable. Defaults to
                TealType.anytype.
            slotId (optional): A scratch slot id that the compiler must store the value.
                This id may be a Python int in the range [0-256).
        """

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

    def index(self) -> Expr:
        return self.slot.index()


ScratchVar.__module__ = "pyteal"


class DynamicScratchVar:
    """
    Example of Dynamic Scratch space whereby the slot index is picked up from the stack:
        .. code-block:: python1

            player_score = DynamicScratchVar(TealType.uint64)

            wilt = ScratchVar(TealType.uint64, 129)
            kobe = ScratchVar(TealType.uint64)
            dt = ScratchVar(TealType.uint64, 131)

            seq = Seq(
                player_score.set_index(wilt),
                player_score.store(Int(100)),
                player_score.set_index(kobe),
                player_score.store(Int(81)),
                player_score.set_index(dt),
                player_score.store(Int(73)),
                Assert(player_score.load() == Int(73)),
                Assert(player_score.index() == Int(131)),
                player_score.set_index(wilt),
                Assert(player_score.load() == Int(100)),
                Assert(player_score.index() == Int(129)),
                Int(100),
            )
    """

    def __init__(
        self,
        ttype: TealType = TealType.anytype,
        # indexer: ScratchVar = None,
    ):
        """Create a new DynamicScratchVar which references other ScratchVar's

        Args:
            ttype (optional): The type that this variable can hold. Defaults to TealType.anytype.
            indexer (optional): A ScratchVar object that holds the _index_ that this DynamicScratchVar is
                using to look up other slots. It is _NOT RECOMMENDED_ that a developer provide this optional
                argument, but instead, to let the compiler construct one dynamically. In rare situations
                it could be useful to provide the ability to explicitly provide the indexer. For example,
                this is needed in the internal PyTEAL compiler code for handling pass-by-reference semantics.
        """
        self.type = ttype
        self.indexer = ScratchVar(TealType.uint64)
        self.slot = self.indexer.slot

    def set_index(self, indexVar: ScratchVar) -> Expr:
        """Set this DynamicScratchVar to reference the provided `indexVar`.
        Followup `store`, `load` and `index` operations will use the provided `indexVar` until
        `set_index()` is called again to reset the referenced ScratchVar.
        """
        return self.indexer.store(indexVar.index())

    def storage_type(self) -> TealType:
        """Get the type of expressions that can be stored in this ScratchVar."""
        return self.type

    def store(self, value: Expr) -> Expr:
        """Store the value in the referenced ScratchVar."""
        require_type(value, self.type)
        index = ScratchLoad(self.indexer.slot, TealType.uint64)
        return ScratchStore(slot=None, value=value, index_expression=index)

    def load(self) -> ScratchLoad:
        """Load the current value from the referenced ScratchVar."""
        index = ScratchLoad(self.indexer.slot, TealType.uint64)
        return ScratchLoad(slot=None, type=self.type, index_expression=index)

    def index(self) -> Expr:
        """Get the index of the referenced ScratchVar."""
        return self.indexer.load()

    def internal_index(self) -> Expr:
        """Get the index of _this_ DynamicScratchVar, as opposed to that of the referenced ScratchVar."""
        return self.indexer.index()


DynamicScratchVar.__module__ = "pyteal"
