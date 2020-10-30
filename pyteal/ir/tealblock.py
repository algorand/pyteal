from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Iterator, TYPE_CHECKING

from ..errors import TealInternalError
from .tealop import TealOp, Op
if TYPE_CHECKING:
    from ..ast import Expr

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
    
    # def __hash__(self) -> int:
    #     return hash((tuple(self.ops), self.trueBlock, self.falseBlock, self.nextBlock))

    @classmethod
    def OpWithArgs(cls, op: TealOp, args: List['Expr']) -> Tuple['TealSimpleBlock', 'TealSimpleBlock']:
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

class TealSimpleBlock(TealBlock):

    def __init__(self, ops: List[TealOp]) -> None:
        super().__init__(ops)
        self.nextBlock: Optional[TealBlock] = None
    
    def setNextBlock(self, block: TealBlock) -> None:
        self.nextBlock = block
    
    def getOutgoing(self) -> List[TealBlock]:
        if self.nextBlock is None:
            return []
        return [self.nextBlock]
    
    def replaceOutgoing(self, oldBlock: TealBlock, newBlock: TealBlock) -> None:
        if self.nextBlock is oldBlock:
            self.nextBlock = newBlock
    
    def __repr__(self) -> str:
        return "TealSimpleBlock({}, next={})".format(
            repr(self.ops),
            repr(self.nextBlock),
        )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealSimpleBlock):
            return False
        return self.ops == other.ops and \
            self.nextBlock == other.nextBlock

class TealConditionalBlock(TealBlock):

    def __init__(self, ops: List[TealOp]) -> None:
        super().__init__(ops)
        self.trueBlock: Optional[TealBlock] = None
        self.falseBlock: Optional[TealBlock] = None
    
    def setTrueBlock(self, block: TealBlock) -> None:
        self.trueBlock = block
    
    def setFalseBlock(self, block: TealBlock) -> None:
        self.falseBlock = block
    
    def getOutgoing(self) -> List[TealBlock]:
        outgoing = []
        if self.trueBlock is not None:
            outgoing.append(self.trueBlock)
        if self.falseBlock is not None:
            outgoing.append(self.falseBlock)
        return outgoing
    
    def replaceOutgoing(self, oldBlock: TealBlock, newBlock: TealBlock) -> None:
        if self.trueBlock is oldBlock:
            self.trueBlock = newBlock
        elif self.falseBlock is oldBlock:
            self.falseBlock = newBlock
    
    def __repr__(self) -> str:
        return "TealConditionalBlock({}, true={}, false={})".format(
            repr(self.ops),
            repr(self.trueBlock),
            repr(self.falseBlock),
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealConditionalBlock):
            return False
        return self.ops == other.ops and \
            self.trueBlock == other.trueBlock and \
            self.falseBlock == other.falseBlock
