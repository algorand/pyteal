from abc import ABC, abstractmethod
from typing import Optional, List, Tuple, Set, Iterator, cast, TYPE_CHECKING

from .tealop import TealOp, Op
from ..errors import TealCompileError

if TYPE_CHECKING:
    from ..ast import Expr, ScratchSlot
    from ..compiler import CompileOptions
    from .tealsimpleblock import TealSimpleBlock


class TealBlock(ABC):
    """Represents a basic block of TealComponents in a graph."""

    def __init__(self, ops: List[TealOp]) -> None:
        self.ops = ops
        self.incoming: List[TealBlock] = []

    @abstractmethod
    def getOutgoing(self) -> List["TealBlock"]:
        """Get this block's children blocks, if any."""
        pass

    @abstractmethod
    def replaceOutgoing(self, oldBlock: "TealBlock", newBlock: "TealBlock") -> None:
        """Replace one of this block's child blocks."""
        pass

    def isTerminal(self) -> bool:
        """Check if this block ends the program."""
        for op in self.ops:
            if op.getOp() in (Op.return_, Op.retsub, Op.err):
                return True
        return len(self.getOutgoing()) == 0

    def validateTree(
        self, parent: "TealBlock" = None, visited: List["TealBlock"] = None
    ) -> None:
        """Check that this block and its children have valid parent pointers.

        Args:
            parent (optional): The parent block to this one, if it has one. Defaults to None.
            visited (optional): Used internally to remember blocks that have been visited. Set to None.
        """
        if visited is None:
            # using a list instead of a set as TealBlock is not hashable and PyTEAL programs should be short anyway
            visited = []

        if parent is not None:
            count = 0
            for block in self.incoming:
                if parent is block:
                    count += 1
            assert count == 1

        if all(self is not b for b in visited):
            # if the block was not already visited
            visited.append(self)
            for block in self.getOutgoing():
                block.validateTree(self, visited)

    def addIncoming(
        self, parent: "TealBlock" = None, visited: List["TealBlock"] = None
    ) -> None:
        """Calculate the parent blocks for this block and its children.

        Args:
            parent (optional): The parent block to this one, if it has one. Defaults to None.
            visited (optional): Used internally to remember blocks that have been visited. Set to None.
        """
        if visited is None:
            # using a list instead of a set as TealBlock is not hashable and PyTEAL programs should be short anyway
            visited = []

        if parent is not None and all(parent is not b for b in self.incoming):
            self.incoming.append(parent)

        if all(self is not b for b in visited):
            # if the block was not already visited
            visited.append(self)
            for b in self.getOutgoing():
                b.addIncoming(self, visited)

    def validateSlots(
        self,
        slotsInUse: Set["ScratchSlot"] = None,
        visited: Set[Tuple[int, ...]] = None,
    ) -> List[TealCompileError]:
        if visited is None:
            visited = set()

        if slotsInUse is None:
            slotsInUse = set()

        currentSlotsInUse = set(slotsInUse)
        errors = []

        for op in self.ops:
            if op.getOp() == Op.store:
                for slot in op.getSlots():
                    currentSlotsInUse.add(slot)

            if op.getOp() == Op.load:
                for slot in op.getSlots():
                    if slot not in currentSlotsInUse:
                        e = TealCompileError(
                            "Scratch slot load occurs before store", op.expr
                        )
                        errors.append(e)

        if not self.isTerminal():
            sortedSlots = sorted(slot.id for slot in currentSlotsInUse)
            for block in self.getOutgoing():
                visitedKey = (id(block), *sortedSlots)
                if visitedKey in visited:
                    continue
                visited.add(visitedKey)

                for error in block.validateSlots(currentSlotsInUse, visited):
                    if error not in errors:
                        errors.append(error)

        return errors

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass

    @classmethod
    def FromOp(
        cls, options: "CompileOptions", op: TealOp, *args: "Expr"
    ) -> Tuple["TealBlock", "TealSimpleBlock"]:
        """Create a path of blocks from a TealOp and its arguments.

        Returns:
            The starting and ending block of the path that encodes the given TealOp and arguments.
        """
        from .tealsimpleblock import TealSimpleBlock

        opBlock = TealSimpleBlock([op])

        if len(args) == 0:
            return opBlock, opBlock

        start = None
        prevArgEnd = None
        for i, arg in enumerate(args):
            argStart, argEnd = arg.__teal__(options)
            if i == 0:
                start = argStart
            else:
                cast(TealSimpleBlock, prevArgEnd).setNextBlock(argStart)
            prevArgEnd = argEnd

        cast(TealSimpleBlock, prevArgEnd).setNextBlock(opBlock)

        return cast(TealBlock, start), opBlock

    @classmethod
    def Iterate(cls, start: "TealBlock") -> Iterator["TealBlock"]:
        """Perform a depth-first search of the graph of blocks starting with start."""
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
    def NormalizeBlocks(cls, start: "TealBlock") -> "TealBlock":
        """Minimize the number of blocks in the graph of blocks starting with start by combining
        sequential blocks. This operation does not alter the operations of the graph or the
        functionality of its underlying program, however it does mutate the input graph.

        Returns:
            The new starting point of the altered graph. May be the same or differant than start.
        """
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

        for block in TealBlock.Iterate(start):
            if len(block.ops) == 0:
                outgoing = block.getOutgoing()
                if len(outgoing) == 1:
                    # if block has 0 ops and 1 outgoing edge, directly connect every incoming block
                    # to the single outgoing block, thereby removing an unnecessary intermediate
                    # jump to this block
                    outgoingBlock = outgoing[0]
                    for i, incomingBlock in enumerate(outgoingBlock.incoming):
                        if block is incomingBlock:
                            # remove block from incoming of outgoing
                            outgoingBlock.incoming.pop(i)
                            break

                    for prev in block.incoming:
                        prev.replaceOutgoing(block, outgoing[0])
                        if id(prev) not in [id(b) for b in outgoingBlock.incoming]:
                            outgoingBlock.incoming.append(prev)

                    if block is start:
                        start = block

        return start


TealBlock.__module__ = "pyteal"
