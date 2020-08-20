from typing import cast, Union, List, TYPE_CHECKING

from .tealcomponent import TealComponent
from .ops import Op
from ..errors import TealInternalError
if TYPE_CHECKING:
    from ..ast import ScratchSlot

class TealOp(TealComponent):
    
    def __init__(self, op: Op, *args: Union[int, str, 'ScratchSlot']) -> None:
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
        parts = [self.op.value]
        for arg in self.args:
            if isinstance(arg, ScratchSlot):
                raise TealInternalError("Slot not assigned: {}".format(arg))
            
            if isinstance(arg, int):
                parts.append(str(arg))
            else:
                parts.append(arg)

        return " ".join(parts)
    
    def __repr__(self) -> str:
        args = [self.op.__str__()]
        for a in self.args:
            args.append(a.__repr__())

        return "TealOp({})".format(", ".join(args))
    
    def __hash__(self) -> int:
        return (self.op, *self.args).__hash__()
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealOp):
            return False
        return self.op == other.op and self.args == other.args

TealOp.__module__ = "pyteal"
