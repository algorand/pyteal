from typing import cast, Union, List, Optional, TYPE_CHECKING

from .tealcomponent import TealComponent
from .ops import Op
from ..errors import TealInternalError
if TYPE_CHECKING:
    from ..ast import Expr, ScratchSlot

class TealOp(TealComponent):
    
    def __init__(self, expr: Optional['Expr'], op: Op, *args: Union[int, str, 'ScratchSlot']) -> None:
        super().__init__(expr)
        self.op = op
        self.args = list(args)
    
    def getOp(self) -> Op:
        return self.op
    
    def getSlots(self) -> List['ScratchSlot']:
        from ..ast import ScratchSlot
        return [arg for arg in self.args if isinstance(arg, ScratchSlot)]
    
    def assignSlot(self, slot: 'ScratchSlot', location: int):
        for i, arg in enumerate(self.args):
            if slot == arg:
                self.args[i] = location

    def assemble(self) -> str:
        from ..ast import ScratchSlot
        parts = [str(self.op)]
        for arg in self.args:
            if isinstance(arg, ScratchSlot):
                raise TealInternalError("Slot not assigned: {}".format(arg))
            
            if isinstance(arg, int):
                parts.append(str(arg))
            else:
                parts.append(arg)

        return " ".join(parts)
    
    def __repr__(self) -> str:
        args = [str(self.op)]
        for a in self.args:
            args.append(repr(a))

        return "TealOp({}, {})".format(self.expr, ", ".join(args))
    
    def __hash__(self) -> int:
        return (self.op, *self.args).__hash__()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealOp):
            return False
        if TealComponent.Context.checkExpr and self.expr is not other.expr:
            return False
        return self.op == other.op and self.args == other.args

TealOp.__module__ = "pyteal"
