from typing import Union

from ..errors import TealInputError, TealInternalError
from ..types import require_type, TealType

from .expr import Expr
from .int import Int
from .scratch import DynamicSlot, ScratchSlot, ScratchLoad, Slot

# TODO: can we change all the references in this repo to builtins as params/vars to stop shadowing python. EG: rename type fields to ttype
ptype = type


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
        ref: "ScratchVar" = None,
    ):
        """Create a new ScratchVar with an optional type and slot index

        Args:
            type (optional): The type that this variable can hold. An error will be thrown if an
                expression with an incompatiable type is stored in this variable. Defaults to
                TealType.anytype.
            slotId (optional): A scratch slot id that the compiler must store the value.
                This id may be a Python int in the range [0-256).
        """

        if not isinstance(type, (TealType, ptype(None))):
            raise TealInputError(
                "slotId of type {} is disallowed".format(ptype(slotId))
            )

        if not isinstance(slotId, (int, Expr, ptype(None))):
            raise TealInputError(
                "slotId of type {} is disallowed".format(ptype(slotId))
            )

        if not isinstance(ref, (ScratchVar, ptype(None))):
            raise TealInternalError(
                "ref must be another ScratchVar but was {}".format(ptype(ref))
            )

        if ref and slotId is not None:
            raise TealInternalError(
                "cannot specify slotId for byReference ScratchVar's as they inherit their ref's slot"
            )

        self.ref: "ScratchVar" = ref

        self.slot: Slot
        if self.ref:
            self.slot = self.ref.slot
        else:
            self.slot = (
                DynamicSlot(slotId) if isinstance(slotId, Expr) else ScratchSlot(slotId)
            )

        self.type = type
        # self._stored = False

    def storage_type(self) -> TealType:
        """Get the type of expressions that can be stored in this ScratchVar."""
        return self.type

    def store(self, value: Expr) -> Expr:
        """Store value in Scratch Space

        Args:
            value: The value to store. Must conform to this ScratchVar's type.
        """
        require_type(value, self.type)
        # self._stored = True
        return self.slot.store(value, byRef=self.byRef())

    def load(self) -> ScratchLoad:
        """Load value from Scratch Space"""
        return self.slot.load(self.type, byRef=self.byRef())

    def index(self) -> Expr:
        if self.byRef():
            return self.ref.index()

        return self.slot.id if self.slot.dynamic() else Int(self.slot.id)

    def byRef(self) -> bool:
        return self.ref is not None

    def newByRef(self, type: TealType = None):
        # if not self._stored:
        #     raise TealInputError("must load into ScratchVar before creating newByRef")
        # self.load()

        if type is None:
            type = self.type

        # TODO: handle DynamicSlots as well
        return ScratchVar(type, ref=self)


ScratchVar.__module__ = "pyteal"
