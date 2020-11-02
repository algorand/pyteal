from typing import Optional, List, cast

from .tealop import TealOp
from .tealblock import TealBlock

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
        if type(other) is not TealConditionalBlock:
            return False
        other = cast(TealConditionalBlock, other)
        return self.ops == other.ops and \
            self.trueBlock == other.trueBlock and \
            self.falseBlock == other.falseBlock

TealConditionalBlock.__module__ = "pyteal"
