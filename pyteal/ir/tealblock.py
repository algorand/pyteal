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
        return self.nextBlock is None and self.trueBlock is None and self.falseBlock is None
    
    def validate(self, parent: 'TealBlock' = None):
        if parent is not None:
            assert any(parent is block for block in self.incoming)

        if self.isTerminal():
            return

        if self.nextBlock is None:
            if self.trueBlock is None:
                raise TealInternalError("True block missing")
            if self.falseBlock is None:
                raise TealInternalError("False block missing")
            self.trueBlock.validate(self)
            self.falseBlock.validate(self)
        else:
            if self.trueBlock is not None:
                raise TealInternalError("Unexpected true block")
            if self.falseBlock is not None:
                raise TealInternalError("Unexpected false block")
            self.nextBlock.validate(self)
    
    def addIncoming(self, block: 'TealBlock' = None):
        if block is not None and all(block is not b for b in self.incoming):
            self.incoming.append(block)

        if self.nextBlock is not None:
            self.nextBlock.addIncoming(self)
        if self.trueBlock is not None:
            self.trueBlock.addIncoming(self)
        if self.falseBlock is not None:
            self.falseBlock.addIncoming(self)
    
    def trim(self):
        if self.nextBlock is not None:
            self.nextBlock.trim()
            if len(self.nextBlock.ops) == 0 and \
                self.nextBlock.trueBlock is None and \
                self.nextBlock.falseBlock is None and \
                self.nextBlock.nextBlock is None:
                self.nextBlock = None
        if self.trueBlock is not None:
            self.trueBlock.trim()
            if len(self.trueBlock.ops) == 0 and \
                self.trueBlock.trueBlock is None and \
                self.trueBlock.falseBlock is None and \
                self.trueBlock.nextBlock is None:
                self.trueBlock = None
        if self.falseBlock is not None:
            self.falseBlock.trim()
            if len(self.falseBlock.ops) == 0 and \
                self.falseBlock.trueBlock is None and \
                self.falseBlock.falseBlock is None and \
                self.falseBlock.nextBlock is None:
                self.falseBlock = None
    
    def __repr__(self) -> str:
        return "TealBlock({}, trueBlock={}, falseBlock={}, nextBlock={})".format(
            self.ops.__repr__(),
            self.trueBlock.__repr__(),
            self.falseBlock.__repr__(),
            self.nextBlock.__repr__()
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealBlock):
            return False
        return self.ops == other.ops and \
            self.trueBlock == other.trueBlock and \
            self.falseBlock == other.falseBlock and \
            self.nextBlock == other.nextBlock
    
    # def __hash__(self) -> int:
    #     return hash((tuple(self.ops), self.trueBlock, self.falseBlock, self.nextBlock))

    @classmethod
    def OpWithArgs(cls, op: TealOp, args: List['Expr']) -> Tuple['TealBlock', 'TealBlock']:
        opBlock = TealBlock([op])

        if len(args) == 0:
            return opBlock, opBlock

        start = None
        prevArgEnd = None
        for i, arg in enumerate(args):
            argStart, argEnd = arg.__teal__()
            if i == 0:
                start = argStart
            else:
                prevArgEnd.setNextBlock(argStart)
            prevArgEnd = argEnd

        prevArgEnd.setNextBlock(opBlock)

        return start, opBlock
    
    @classmethod
    def Iterate(cls, start: 'TealBlock') -> Iterator['TealBlock']:
        queue = [start]
        visited = list(queue)

        def is_in_visited(block):
            for v in visited:
                if block is v:
                    return True
            return False

        while len(queue) != 0:
            w = queue.pop(0)
            yield w
            for nextBlock in (w.nextBlock, w.trueBlock, w.falseBlock):
                if nextBlock is not None and not is_in_visited(nextBlock):
                    visited.append(nextBlock)
                    queue.append(nextBlock)
    
    @classmethod
    def NormalizeBlocks(cls, start: 'TealBlock'):
        for block in TealBlock.Iterate(start):
            if len(block.incoming) == 1 and block.incoming[0].nextBlock is block:
                # combine blocks
                prev = block.incoming[0]
                prev.ops += block.ops
                prev.nextBlock = block.nextBlock
                prev.trueBlock = block.trueBlock
                prev.falseBlock = block.falseBlock
                for nextBlock in (block.nextBlock, block.trueBlock, block.falseBlock):
                    if nextBlock is not None:
                        i = nextBlock.incoming.index(block)
                        nextBlock.incoming[i] = prev
