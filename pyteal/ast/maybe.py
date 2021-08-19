from typing import List, Union, TYPE_CHECKING

from ..types import TealType
from ..ir import TealOp, Op, TealBlock
from .expr import Expr
from .leafexpr import LeafExpr
from .scratch import ScratchSlot, ScratchLoad

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class MaybeValue(LeafExpr):
    """Represents a get operation returning a value that may not exist."""

    def __init__(
        self,
        op: Op,
        type: TealType,
        *,
        immediate_args: List[Union[int, str]] = None,
        args: List[Expr] = None
    ):
        """Create a new MaybeValue.

        Args:
            op: The operation that returns values.
            type: The type of the returned value.
            immediate_args (optional): Immediate arguments for the op. Defaults to None.
            args (optional): Stack arguments for the op. Defaults to None.
        """
        super().__init__()
        self.op = op
        self.type = type
        self.immediate_args = immediate_args if immediate_args is not None else []
        self.args = args if args is not None else []
        self.slotOk = ScratchSlot()
        self.slotValue = ScratchSlot()

    def hasValue(self) -> ScratchLoad:
        """Check if the value exists.

        This will return 1 if the value exists, otherwise 0.
        """
        return self.slotOk.load(TealType.uint64)

    def value(self) -> ScratchLoad:
        """Get the value.

        If the value exists, it will be returned. Otherwise, the zero value for this type will be
        returned (i.e. either 0 or an empty byte string, depending on the type).
        """
        return self.slotValue.load(self.type)

    def __str__(self):
        ret_str = "(({}".format(self.op)
        for a in self.immediate_args:
            ret_str += " " + a.__str__()

        for a in self.args:
            ret_str += " " + a.__str__()
        ret_str += ") "

        storeOk = self.slotOk.store()
        storeValue = self.slotValue.store()

        ret_str += storeOk.__str__() + " " + storeValue.__str__() + ")"

        return ret_str

    def __teal__(self, options: "CompileOptions"):
        tealOp = TealOp(self, self.op, *self.immediate_args)
        callStart, callEnd = TealBlock.FromOp(options, tealOp, *self.args)

        storeOk = self.slotOk.store()
        storeValue = self.slotValue.store()

        storeOkStart, storeOkEnd = storeOk.__teal__(options)
        storeValueStart, storeValueEnd = storeValue.__teal__(options)

        callEnd.setNextBlock(storeOkStart)
        storeOkEnd.setNextBlock(storeValueStart)

        return callStart, storeValueEnd

    def type_of(self):
        return TealType.none


MaybeValue.__module__ = "pyteal"
