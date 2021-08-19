from typing import List, DefaultDict, cast
from collections import defaultdict

from ..ir import (
    Op,
    TealOp,
    TealLabel,
    TealComponent,
    TealBlock,
    TealSimpleBlock,
    TealConditionalBlock,
)
from ..errors import TealInternalError


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

            nextIndex = blocks.index(simpleBlock.nextBlock, i + 1)
            if nextIndex != i + 1:
                references[nextIndex] += 1
                code.append(TealOp(None, Op.b, indexToLabel(nextIndex)))
        elif type(block) is TealConditionalBlock:
            conditionalBlock = cast(TealConditionalBlock, block)
            assert conditionalBlock.trueBlock is not None
            assert conditionalBlock.falseBlock is not None

            trueIndex = blocks.index(conditionalBlock.trueBlock, i + 1)
            falseIndex = blocks.index(conditionalBlock.falseBlock, i + 1)

            if falseIndex == i + 1:
                references[trueIndex] += 1
                code.append(TealOp(None, Op.bnz, indexToLabel(trueIndex)))
                continue

            if trueIndex == i + 1:
                references[falseIndex] += 1
                code.append(TealOp(None, Op.bz, indexToLabel(falseIndex)))
                continue

            references[trueIndex] += 1
            code.append(TealOp(None, Op.bnz, indexToLabel(trueIndex)))

            references[falseIndex] += 1
            code.append(TealOp(None, Op.b, indexToLabel(falseIndex)))
        else:
            raise TealInternalError("Unrecognized block type: {}".format(type(block)))

    teal: List[TealComponent] = []
    for i, code in enumerate(codeblocks):
        if references[i] != 0:
            teal.append(TealLabel(None, indexToLabel(i)))
        teal += code

    return teal
