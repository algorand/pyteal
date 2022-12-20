from pyteal.errors import TealInputError
from pyteal.types import TealType, require_type

from pyteal.ast.abstractvar import AbstractVar
from pyteal.ast.expr import Expr
from pyteal.ast.scratch import ScratchSlot, ScratchLoad, ScratchStore


class ScratchVar(AbstractVar):
    """
    Interface around Scratch space, similar to get/put local/global state

    Example:
        .. code-block:: python

            myvar = ScratchVar(TealType.uint64)
            Seq([
                myvar.store(Int(5)),
                Assert(myvar.load() == Int(5))
            ])
    """

    def __init__(self, type: TealType = TealType.anytype, slotId: int | None = None):
        """Create a new ScratchVar with an optional type.

        Args:
            type (optional): The type that this variable can hold. An error will be thrown if an
                expression with an incompatible type is stored in this variable. Defaults to
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


class DynamicScratchVar(ScratchVar):
    """
    Example of Dynamic Scratch space whereby the slot index is picked up from the stack:
        .. code-block:: python

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

    def __init__(self, ttype: TealType = TealType.anytype):
        """Create a new DynamicScratchVar which references other ScratchVar's

        Args:
            ttype (optional): The type that this variable can hold. Defaults to TealType.anytype.
        """
        super().__init__(TealType.uint64)
        self.dynamic_type = ttype  # differentiates from ScratchVar.type

    def set_index(self, index_var: ScratchVar) -> Expr:
        """Set this DynamicScratchVar to reference the provided `index_var`.
        Followup `store`, `load` and `index` operations will use the provided `index_var` until
        `set_index()` is called again to reset the referenced ScratchVar.
        """
        # Explanatory comment per Issue #242: Preliminary evidence shows that letting users
        # pass in any ScratchVar subtype (i.e. DynamicScratchVar) may in fact work.
        # However, we are leaving this guard in place pending further investigation.
        # TODO: gain confidence that DynamicScratchVar can be used here and
        # modify the below strict type equality to `isinstance(index_var, ScratchVar)`
        if type(index_var) is not ScratchVar:
            raise TealInputError(
                "Only allowed to use ScratchVar objects for setting indices, but was given a {}".format(
                    type(index_var)
                )
            )

        return super().store(index_var.index())

    def storage_type(self) -> TealType:
        """Get the type of expressions that can be stored in this ScratchVar."""
        return self.dynamic_type

    def store(self, value: Expr) -> Expr:
        """Store the value in the referenced ScratchVar."""

        require_type(value, self.dynamic_type)
        return ScratchStore(slot=None, value=value, index_expression=self.index())

    def load(self) -> ScratchLoad:
        """Load the current value from the referenced ScratchVar."""
        return ScratchLoad(
            slot=None, type=self.dynamic_type, index_expression=self.index()
        )

    def index(self) -> Expr:
        """Get the index of the referenced ScratchVar."""
        return super().load()

    def internal_index(self) -> Expr:
        """Get the index of _this_ DynamicScratchVar, as opposed to that of the referenced ScratchVar."""
        return super().index()


DynamicScratchVar.__module__ = "pyteal"
