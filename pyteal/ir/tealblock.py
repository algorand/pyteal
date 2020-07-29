from typing import Optional, List, Tuple, Iterator, TYPE_CHECKING

from ..errors import TealInternalError
from .tealop import TealOp, Op
if TYPE_CHECKING:
    from ..ast import Expr

class TealBlock:

    def __init__(self, ops: List[TealOp]) -> None:
        self.ops = ops
        self.trueBlock: Optional['TealBlock'] = None
        self.falseBlock: Optional['TealBlock'] = None
        self.nextBlock: Optional['TealBlock'] = None
        self.incoming: List[TealBlock] = []
    
    def setTrueBlock(self, block: 'TealBlock'):
        self.trueBlock = block

    def setFalseBlock(self, block: 'TealBlock'):
        self.falseBlock = block

    def setNextBlock(self, block: 'TealBlock'):
        self.nextBlock = block
    
    def isTerminal(self) -> bool:
        for op in self.ops:
            if op.getOp() in (Op.return_, Op.err):
                return True
        return False
    
    def validate(self):
        if self.isTerminal():
            return

        if self.nextBlock is None:
            if self.trueBlock is None:
                raise TealInternalError("True block missing")
            if self.falseBlock is None:
                raise TealInternalError("False block missing")
            self.trueBlock.validate()
            self.falseBlock.validate()
        else:
            if self.trueBlock is not None:
                raise TealInternalError("Unexpected true block")
            if self.falseBlock is not None:
                raise TealInternalError("Unexpected false block")
            self.nextBlock.validate()
    
    def addIncoming(self, block: 'TealBlock' = None):
        if block is not None and block not in self.incoming:
            self.incoming.append(block)

        if self.isTerminal():
            return

        if self.nextBlock is None:
            assert self.trueBlock is not None and self.falseBlock is not None
            self.trueBlock.addIncoming(self)
            self.falseBlock.addIncoming(self)
        else:
            self.nextBlock.addIncoming(self)

    def normalize(self):
        if len(self.incoming) == 1 and self == self.incoming[0].nextBlock:
            # combine blocks
            self.incoming[0].ops += self.ops
            self.incoming[0].nextBlock = self.nextBlock
            self.incoming[0].trueBlock = self.trueBlock
            self.incoming[0].falseBlock = self.falseBlock
    
    @classmethod
    def OpWithArgs(cls, op: TealOp, args: List['Expr']) -> Tuple['TealBlock', 'TealBlock']:
        start = None
        prevArgEnd = None
        for i, arg in enumerate(args):
            argStart, argEnd = arg.__teal__()
            if i == 0:
                start = argStart
            else:
                prevArgEnd.setNextBlock(argStart)
            prevArgEnd = argEnd

        opBlock = TealBlock([op])
        prevArgEnd.setNextBlock(opBlock)

        return start, opBlock
    
    @classmethod
    def Iterate(cls, start: 'TealBlock') -> Iterator['TealBlock']:
        queue = [start]
        visited = set(queue)
        while len(queue) != 0:
            w = queue.pop(0)
            yield w
            for nextBlock in (w.nextBlock, w.trueBlock, w.falseBlock):
                if nextBlock is not None and nextBlock not in visited:
                    visited.add(nextBlock)
                    queue.append(nextBlock)
