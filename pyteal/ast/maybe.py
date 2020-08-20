from typing import List, Union

from ..types import TealType
from ..ir import TealOp, Op
from .expr import Expr
from .leafexpr import LeafExpr
from .scratch import ScratchSlot, ScratchLoad

class MaybeValue(LeafExpr):
    """Represents a get operation returning a value that may not exist."""

    def __init__(self, op: Op, type: TealType, *, immediate_args: List[Union[int, str]] = None, args: List[Expr] = None):
        """Create a new MaybeValue.

        Args:
            op: The operation that returns values.
            type: The type of the returned value.
            immediate_args (optional): Immediate arguments for the op. Defaults to None.
            args (optional): Stack arguments for the op. Defaults to None.
        """
        self.op = op
        self.type = type
        if immediate_args != None:
            self.immediate_args = immediate_args
        else:
            self.immediate_args = []
        if args != None:
            self.args = args
        else:
            self.args = []
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
    
    def __teal__(self):
        teal = []
        for arg in self.args:
            teal += arg.__teal__()
        teal.append(TealOp(self.op, *self.immediate_args))

        storeOk = self.slotOk.store()
        storeValue = self.slotValue.store()

        teal += storeOk.__teal__()
        teal += storeValue.__teal__()

        return teal

    def type_of(self):
        return TealType.none

MaybeValue.__module__ = "pyteal"
