from typing import List, DefaultDict, cast
from collections import defaultdict

from .ast import Expr
from .ir import Op, Mode, TealComponent, TealOp, TealLabel, TealBlock, TealSimpleBlock, TealConditionalBlock
from .errors import TealInputError, TealInternalError
from .config import NUM_SLOTS

def sortBlocks(start: TealBlock) -> List[TealBlock]:
    """Topologically sort the graph which starts with the input TealBlock.

    Args:
        start: The starting point of the graph to sort.

    Returns:
        An ordered list of TealBlocks that is sorted such that every block is guaranteed to appear
        in the list before all of its outgoing blocks.
    """
    # based on Kahn's algorithm from https://en.wikipedia.org/wiki/Topological_sorting
    S = [start]
    order = []

    while len(S) != 0:
        n = S.pop(0)
        order.append(n)
        for i, m in enumerate(n.getOutgoing()):
            for i, block in enumerate(m.incoming):
                if n is block:
                    m.incoming.pop(i)
                    break
            if len(m.incoming) == 0:
                if i == 0:
                    S.insert(0, m)
                else:
                    S.append(m)
    
    return order

def flattenBlocks(blocks: List[TealBlock]) -> List[TealComponent]:
    """Lowers a list of TealBlocks into a list of TealComponents.

    Args:
        blocks: The blocks to lower.
    """
    codeblocks = []
    references: DefaultDict[int, int] = defaultdict(int)

    indexToLabel = lambda index: "l{}".format(index)

    for i, block in enumerate(blocks):
        code = list(block.ops)
        codeblocks.append(code)
        if block.isTerminal():
            continue

        if type(block) is TealSimpleBlock:
            simpleBlock = cast(TealSimpleBlock, block)
            assert simpleBlock.nextBlock is not None

            nextIndex = blocks.index(simpleBlock.nextBlock, i+1)
            if nextIndex != i + 1:
                references[nextIndex] += 1
                code.append(TealOp(Op.b, indexToLabel(nextIndex)))
        elif type(block) is TealConditionalBlock:
            conditionalBlock = cast(TealConditionalBlock, block)
            assert conditionalBlock.trueBlock is not None
            assert conditionalBlock.falseBlock is not None

            trueIndex = blocks.index(conditionalBlock.trueBlock, i+1)
            falseIndex = blocks.index(conditionalBlock.falseBlock, i+1)

            if falseIndex == i + 1:
                references[trueIndex] += 1
                code.append(TealOp(Op.bnz, indexToLabel(trueIndex)))
                continue

            if trueIndex == i + 1:
                references[falseIndex] += 1
                code.append(TealOp(Op.bz, indexToLabel(falseIndex)))
                continue

            references[trueIndex] += 1
            code.append(TealOp(Op.bnz, indexToLabel(trueIndex)))

            references[falseIndex] += 1
            code.append(TealOp(Op.b, indexToLabel(falseIndex)))
        else:
            raise TealInternalError("Unrecognized block type: {}".format(type(block)))

    teal: List[TealComponent] = []
    for i, code in enumerate(codeblocks):
        if references[i] != 0:
            teal.append(TealLabel(indexToLabel(i)))
        teal += code

    return teal

def verifyOpsForMode(teal: List[TealComponent], mode: Mode):
    """Verify that all TEAL operations are allowed in mode.

    Args:
        teal: Code to check.
        mode: The mode to check against.

    Raises:
        TealInputError: if teal contains an operation not allowed in mode.
    """
    for stmt in teal:
        if isinstance(stmt, TealOp):
            op = stmt.getOp()
            if not op.mode & mode:
                raise TealInputError("Op not supported in {} mode: {}".format(mode.name, op.value))

def compileTeal(ast: Expr, mode: Mode) -> str:
    """Compile a PyTeal expression into TEAL assembly.

    Args:
        ast: The PyTeal expression to assemble.

    Returns:
        str: A TEAL assembly program compiled from the input expression.

    Raises:
        TealInputError: if an operation in ast is not supported by the supplied mode.
    """
    start, _ = ast.__teal__()
    start.addIncoming()
    start.validate()

    start = TealBlock.NormalizeBlocks(start)
    start.validate()

    order = sortBlocks(start)
    teal = flattenBlocks(order)

    verifyOpsForMode(teal, mode)

    slots = set()
    for stmt in teal:
        for slot in stmt.getSlots():
            slots.add(slot)
    
    if len(slots) > NUM_SLOTS:
        # TODO: identify which slots can be reused
        raise TealInternalError("Too many slots in use: {}, maximum is {}".format(slots, NUM_SLOTS))
    
    # TODO: convert slots to a list with a defined order so that generated code is deterministic
    location = 0
    while len(slots) > 0:
        slot = slots.pop()
        for stmt in teal:
            stmt.assignSlot(slot, location)
        location += 1

    lines = ["#pragma version 2"]
    lines += [i.assemble() for i in teal]
    return "\n".join(lines)
