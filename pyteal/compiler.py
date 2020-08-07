from typing import List, DefaultDict
from collections import defaultdict

from .ast import Expr
from .ir import Mode, TealComponent, TealOp, TealLabel, TealBlock, Op
from .errors import TealInputError, TealInternalError

NUM_SLOTS = 256

def sortBlocks(start: TealBlock) -> List[TealBlock]:
    S = [start]
    order = []

    while len(S) != 0:
        n = S.pop(0)
        order.append(n)
        if n.isTerminal():
            continue
        for m in (n.nextBlock, n.falseBlock, n.trueBlock):
            if m is None:
                continue
            m.incoming.remove(n)
            if len(m.incoming) == 0:
                if m is n.trueBlock:
                    S.append(m)
                else:
                    S.insert(0, m)
    
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

        if block.nextBlock is not None:
            nextIndex = blocks.index(block.nextBlock)
            if nextIndex != i + 1:
                references[nextIndex] += 1
                code.append(TealOp(Op.b, indexToLabel(nextIndex)))
        else:
            trueIndex = blocks.index(block.trueBlock)
            falseIndex = blocks.index(block.falseBlock)

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

    TealBlock.NormalizeBlocks(start)
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
        raise TealInternalError("Not yet implemented")
    
    location = 0
    while len(slots) > 0:
        slot = slots.pop()
        for stmt in teal:
            stmt.assignSlot(slot, location)
        location += 1

    lines = ["#pragma version 2"]
    lines += [i.assemble() for i in teal]
    return "\n".join(lines)
