from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Iterator, cast, TYPE_CHECKING

from .tealop import TealOp, Op
if TYPE_CHECKING:
    from ..ast import Expr
    from .tealsimpleblock import TealSimpleBlock

class TealBlock(ABC):

    def __init__(self, ops: List[TealOp]) -> None:
        self.ops = ops
        self.incoming: List[TealBlock] = []
    
    @abstractmethod
    def getOutgoing(self) -> List['TealBlock']:
        pass

    @abstractmethod
    def replaceOutgoing(self, oldBlock: 'TealBlock', newBlock: 'TealBlock') -> None:
        pass
    
    def isTerminal(self) -> bool:
        for op in self.ops:
            if op.getOp() in (Op.return_, Op.err):
                return True
        return len(self.getOutgoing()) == 0
    
    def validate(self, parent: 'TealBlock' = None) -> None:
        if parent is not None:
            count = 0
            for block in self.incoming:
                if parent is block:
                    count += 1
            assert count == 1
        
        for block in self.getOutgoing():
            block.validate(self)
    
    def addIncoming(self, block: 'TealBlock' = None) -> None:
        if block is not None and all(block is not b for b in self.incoming):
            self.incoming.append(block)
        
        for block in self.getOutgoing():
            block.addIncoming(self)
    
    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass

    @classmethod
    def FromOp(cls, op: TealOp, *args: 'Expr') -> Tuple['TealBlock', 'TealSimpleBlock']:
        from .tealsimpleblock import TealSimpleBlock
        opBlock = TealSimpleBlock([op])

        if len(args) == 0:
            return opBlock, opBlock

        start = None
        prevArgEnd = None
        for i, arg in enumerate(args):
            argStart, argEnd = arg.__teal__()
            if i == 0:
                start = argStart
            else:
                cast(TealSimpleBlock, prevArgEnd).setNextBlock(argStart)
            prevArgEnd = argEnd

        cast(TealSimpleBlock, prevArgEnd).setNextBlock(opBlock)

        return cast(TealBlock, start), opBlock
    
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
            nextBlocks = w.getOutgoing()
            yield w
            for nextBlock in nextBlocks:
                if not is_in_visited(nextBlock):
                    visited.append(nextBlock)
                    queue.append(nextBlock)
    
    @classmethod
    def NormalizeBlocks(cls, start: 'TealBlock') -> 'TealBlock':
        for block in TealBlock.Iterate(start):
            if len(block.incoming) == 1:
                prev = block.incoming[0]
                prevOutgoing = prev.getOutgoing()
                if len(prevOutgoing) == 1 and prevOutgoing[0] is block:
                    # combine blocks
                    block.ops = prev.ops + block.ops
                    block.incoming = prev.incoming
                    for incoming in prev.incoming:
                        incoming.replaceOutgoing(prev, block)
                    if prev is start:
                        start = block
        
        return start

TealBlock.__module__ = "pyteal"
