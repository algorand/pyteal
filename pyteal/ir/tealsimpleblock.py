from typing import Optional, List, cast

from .tealop import TealOp
from .tealblock import TealBlock

class TealSimpleBlock(TealBlock):
    """Represents a basic block of TealComponents in a graph that does not contain a branch condition."""

    def __init__(self, ops: List[TealOp]) -> None:
        super().__init__(ops)
        self.nextBlock: Optional[TealBlock] = None
        self.visiting = []

    def setNextBlock(self, block: TealBlock) -> None:
        """Set the block that follows this one."""
        self.nextBlock = block
    
    def getOutgoing(self) -> List[TealBlock]:
        if self.nextBlock is None:
            return []
        return [self.nextBlock]
    
    def replaceOutgoing(self, oldBlock: TealBlock, newBlock: TealBlock) -> None:
        if self.nextBlock is oldBlock:
            self.nextBlock = newBlock
    
    def __repr__(self) -> str:
        if self.nextBlock in self.visiting:
            return "TealSimpleBlock({}, next={})".format(
                repr(self.ops),
                "",
            )
        self.visiting.append(self.nextBlock)
        blockstr = "TealSimpleBlock({}, next={})".format(
            repr(self.ops),
            repr(self.nextBlock),
        )
        self.visiting.pop()
        return blockstr
    
    def __eq__(self, other: object) -> bool:
        if type(other) is not TealSimpleBlock:
            return False
        other = cast(TealSimpleBlock, other)
        return self.ops == other.ops and \
            self.nextBlock == other.nextBlock

TealSimpleBlock.__module__ = "pyteal"
