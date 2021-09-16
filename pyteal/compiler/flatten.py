from typing import List, Dict, DefaultDict, Optional, cast
from collections import defaultdict

from ..ast import SubroutineDefinition
from ..ir import (
    Op,
    TealOp,
    TealLabel,
    TealComponent,
    TealBlock,
    TealSimpleBlock,
    TealConditionalBlock,
    LabelReference,
)
from ..errors import TealInternalError


def flattenBlocks(blocks: List[TealBlock]) -> List[TealComponent]:
    """Lowers a list of TealBlocks into a list of TealComponents.

    Args:
        blocks: The blocks to lower.
    """
    codeblocks = []
    references: DefaultDict[int, int] = defaultdict(int)

    labelRefs: Dict[int, LabelReference] = dict()

    def indexToLabel(index: int) -> LabelReference:
        if index not in labelRefs:
            labelRefs[index] = LabelReference("l{}".format(index))
        return labelRefs[index]

    def blockIndexByReference(block: TealBlock) -> int:
        for i, b in enumerate(blocks):
            if block is b:
                return i
        raise ValueError("Block not present in list: {}".format(block))

    for i, block in enumerate(blocks):
        code = list(block.ops)
        codeblocks.append(code)
        if block.isTerminal():
            continue

        if type(block) is TealSimpleBlock:
            assert block.nextBlock is not None

            nextIndex = blockIndexByReference(block.nextBlock)

            if nextIndex != i + 1:
                references[nextIndex] += 1
                code.append(TealOp(None, Op.b, indexToLabel(nextIndex)))

        elif type(block) is TealConditionalBlock:
            assert block.trueBlock is not None
            assert block.falseBlock is not None

            trueIndex = blockIndexByReference(block.trueBlock)
            falseIndex = blockIndexByReference(block.falseBlock)

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


def flattenSubroutines(
    subroutineMapping: Dict[Optional[SubroutineDefinition], List[TealComponent]],
    subroutineToLabel: Dict[SubroutineDefinition, str],
) -> List[TealComponent]:
    """Combines each subroutine's list of TealComponents into a single list of TealComponents that
    represents the entire program.

    Args:
        subroutineMapping: A dictionary containing a list of TealComponents for every subroutine in
            a program. The key None is taken to indicate the main program routine.
        subroutineToLabel: An ordered dictionary which resolves each subroutine to a string label.

    Returns:
        A single list of TealComponents representing the entire program.
    """
    combinedOps: List[TealComponent] = []

    # By default all branch labels in each subroutine will start from "l0". To
    # make each subroutine have unique labels, we prefix "main_" to the ones
    # from the main routine, and "subX_" (the subroutine label) to the
    # ones from each subroutine

    mainRoutine = subroutineMapping[None]
    for stmt in mainRoutine:
        if isinstance(stmt, TealLabel):
            stmt.getLabelRef().addPrefix("main_")
    combinedOps += mainRoutine

    for subroutine, label in subroutineToLabel.items():
        comment = subroutine.name()
        labelPrefix = label + "_"

        subroutineOps = subroutineMapping[subroutine]
        for stmt in subroutineOps:
            if isinstance(stmt, TealLabel):
                stmt.getLabelRef().addPrefix(labelPrefix)

        combinedOps.append(TealLabel(None, LabelReference(label), comment))
        combinedOps += subroutineOps

    return combinedOps
