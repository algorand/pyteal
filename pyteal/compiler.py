from typing import List, DefaultDict, cast
from collections import defaultdict

from .ast import Expr
from .ir import Op, Mode, TealComponent, TealOp, TealLabel, TealBlock, TealSimpleBlock, TealConditionalBlock
from .errors import TealInputError, TealInternalError
from .config import NUM_SLOTS

def sortBlocks(start: TealBlock) -> List[TealBlock]:
    # based on Kahn's algorithm from https://en.wikipedia.org/wiki/Topological_sorting

    S = [start]
    order = []

    while len(S) != 0:
        n = S.pop(0)
        order.append(n)
        for m in n.getOutgoing():
            for i, block in enumerate(m.incoming):
                if n is block:
                    m.incoming.pop(i)
                    break
            if len(m.incoming) == 0:
                S.append(m)
    
    return order

def flattenBlocks(blocks: List[TealBlock]) -> List[TealComponent]:
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
            nextIndex = blocks.index(simpleBlock.nextBlock, i+1)
            if nextIndex != i + 1:
                references[nextIndex] += 1
                code.append(TealOp(Op.b, indexToLabel(nextIndex)))
        elif type(block) is TealConditionalBlock:
            conditionalBlock = cast(TealConditionalBlock, block)
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
    
    location = 0
    while len(slots) > 0:
        slot = slots.pop()
        for stmt in teal:
            stmt.assignSlot(slot, location)
        location += 1

    lines = ["#pragma version 2"]
    lines += [i.assemble() for i in teal]
    return "\n".join(lines)
