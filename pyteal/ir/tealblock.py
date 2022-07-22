from abc import ABC, abstractmethod

from typing import Dict, List, Tuple, Set, Iterator, cast, TYPE_CHECKING

from pyteal.ir.tealop import TealOp, Op
from pyteal.errors import TealCompileError

if TYPE_CHECKING:
    from pyteal.ast import Expr, ScratchSlot
    from pyteal.compiler import CompileOptions
    from pyteal.ir.tealsimpleblock import TealSimpleBlock


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
        from pyteal.ir.tealsimpleblock import TealSimpleBlock

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
        """Perform a breadth-first search of the graph of blocks starting with start."""
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

    @classmethod
    def GetReferencedScratchSlots(cls, start: "TealBlock") -> List["ScratchSlot"]:
        """Get all scratch slot references for the graph starting at this TealBlock.

        Returns:
            A list of ScratchSlots where each element represents a reference to that slot by a
            TealOp in the graph. The order of the list is consistent, and there may be duplicate
            ScratchSlots in the list if the same slot is referenced multiple times.
        """
        slots: List[ScratchSlot] = []

        for block in TealBlock.Iterate(start):
            for op in block.ops:
                slots += op.getSlots()

        return slots

    @classmethod
    def MatchScratchSlotReferences(
        cls, actual: List["ScratchSlot"], expected: List["ScratchSlot"]
    ) -> bool:
        """Determine if there is a mapping between the actual and expected lists of ScratchSlots.

        A mapping is defined as follows:
          * The actual and expected lists must have the same length.
          * For every ScratchSlot referenced by either list:

            * If the slot appears in both lists, it must appear the exact same number of times and at
              the exact same indexes in both lists.

            * If the slot appears only in one list, for each of its appearances in that list, there
              must be a ScratchSlot in the other list that appears the exact same number of times
              and at the exact same indexes.

        Returns:
            True if and only if a mapping as described above exists between actual and expected.
        """
        if len(actual) != len(expected):
            return False

        commonSlots = set(actual) & set(expected)
        mapFromActualToExpected: Dict[ScratchSlot, ScratchSlot] = {
            slot: slot for slot in commonSlots
        }

        for actualSlot, expectedSlot in zip(actual, expected):
            if actualSlot not in mapFromActualToExpected:
                if expectedSlot in mapFromActualToExpected.values():
                    # this value was already seen
                    return False
                mapFromActualToExpected[actualSlot] = expectedSlot
                continue

            if mapFromActualToExpected[actualSlot] != expectedSlot:
                return False

        return True


TealBlock.__module__ = "pyteal"
