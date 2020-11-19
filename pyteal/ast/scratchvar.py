from ..types import TealType, require_type
from ..ir import TealOp, Op, TealBlock
from .leafexpr import LeafExpr
from .expr import Expr
from .scratch import ScratchSlot


class ScratchVar:
    """
    Interface around Scratch space, similiar to get/put local/global state
    >>> myvar = ScratchVar()
    >>> Seq([myvar.store(Int(5)), Assert(myvar.load() == Int(5))])
    """
    def __init__(self):
        self.slot = ScratchSlot()

    def store(self, value: Expr) -> 'ScratchVarStore':
        """Store value in Scratch Space"""
        return ScratchVarStore(self.slot, value)

    def load(self) -> 'ScrachVarLoad':
        """Load value from Scratch Space"""
        return ScrachVarLoad(self.slot)

    def __eq__(self, other):
        return self.__eq__(other)


class ScratchVarStore(LeafExpr):
    """
    Expression to store value in Scratch Space
    """
    def __init__(self, slot: ScratchSlot, value: Expr):
        require_type(value.type_of(), TealType.anytype)
        self.slot = slot
        self.value = value

    def __teal__(self):
        return TealBlock.FromOp(TealOp(Op.store, self.slot), self.value)

    def type_of(self) -> TealType:
        return TealType.none

    def __str__(self):
        return "(ScratchVarStore {} {})".format(self.slot, self.value)


class ScrachVarLoad(LeafExpr):
    """Expression to load value from Scratch Space"""
    def __init__(self, slot: ScratchSlot):
        self.slot = slot

    def __teal__(self):
        return TealBlock.FromOp(TealOp(Op.load, self.slot))

    def type_of(self) -> TealType:
        return TealType.anytype

    def __str__(self):
        return "(ScrachVarLoad {})".format(self.slot)
