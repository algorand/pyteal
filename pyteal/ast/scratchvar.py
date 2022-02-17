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
        indexer: ScratchVar = None,
    ):

        self.type = ttype
        if indexer is None:
            indexer = ScratchVar(TealType.uint64)

        self.indexer: ScratchVar
        self.slot: ScratchSlot
        self._set_indexer(indexer)

    def _set_indexer(self, indexer: ScratchVar) -> None:
        if not isinstance(indexer, ScratchVar):
            raise TealInternalError(
                "indexer must be a ScratchVar but had python type {}".format(
                    type(indexer)
                )
            )

        if indexer.type != TealType.uint64:
            raise TealInternalError(
                "indexer must have teal type uint64 but was {} instead".format(
                    indexer.type
                )
            )

        self.indexer = indexer
        self.slot = self.indexer.slot

    def set_index(self, indexVar: ScratchVar) -> Expr:
        return self.indexer.store(indexVar.index())

    def store(self, value: Expr) -> Expr:
        index = ScratchLoad(self.indexer.slot, TealType.uint64)
        return ScratchStore(slot=None, value=value, index_expression=index)

    def load(self) -> ScratchLoad:
        index = ScratchLoad(self.indexer.slot, TealType.uint64)
        return ScratchLoad(slot=None, type=self.type, index_expression=index)

    def index(self) -> Expr:
        return self.indexer.load()

    def internal_index(self) -> Expr:
        return self.indexer.index()


DynamicScratchVar.__module__ = "pyteal"
