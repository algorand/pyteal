from typing import List

from pyteal.ir.tealop import TealOp
from pyteal.ir.tealblock import TealBlock


class TealConditionalBlock(TealBlock):
    """Represents a basic block of TealComponents in a graph ending with a branch condition."""

    def __init__(self, ops: List[TealOp], root_expr: "Expr | None" = None) -> None:  # type: ignore
        super().__init__(ops, root_expr=root_expr)
        self.trueBlock: TealBlock | None = None
        self.falseBlock: TealBlock | None = None

    def setTrueBlock(self, block: TealBlock) -> None:
        """Set the block that this one should branch to if its condition is true."""
        self.trueBlock = block

    def setFalseBlock(self, block: TealBlock) -> None:
        """Set the block that this one should branch to if its condition is false."""
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
        return "TealConditionalBlock({}, true={}, false={}, conditional={})".format(
            repr(self.ops),
            repr(self.trueBlock),
            repr(self.falseBlock),
            repr(self._sframes_container),
        )

    def __eq__(self, other: object) -> bool:
        if type(other) is not TealConditionalBlock:
            return False
        return (
            self.ops == other.ops
            and self.trueBlock == other.trueBlock
            and self.falseBlock == other.falseBlock
        )


TealConditionalBlock.__module__ = "pyteal"
