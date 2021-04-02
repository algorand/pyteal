from typing import List, DefaultDict, cast
from collections import defaultdict

from .ast import Expr
from .ir import Op, Mode, TealComponent, TealOp, TealLabel, TealBlock, TealSimpleBlock, TealConditionalBlock
from .errors import TealInputError, TealInternalError
from .config import NUM_SLOTS

MAX_TEAL_VERSION = 3
MIN_TEAL_VERSION = 2
DEFAULT_TEAL_VERSION = MIN_TEAL_VERSION

class CompileOptions:

    def __init__(self, *, mode: Mode = Mode.Signature, version: int = DEFAULT_TEAL_VERSION):
        self.mode = mode
        self.version = version

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
                code.append(TealOp(None, Op.b, indexToLabel(nextIndex)))
        elif type(block) is TealConditionalBlock:
            conditionalBlock = cast(TealConditionalBlock, block)
            assert conditionalBlock.trueBlock is not None
            assert conditionalBlock.falseBlock is not None

            trueIndex = blocks.index(conditionalBlock.trueBlock, i+1)
            falseIndex = blocks.index(conditionalBlock.falseBlock, i+1)

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

def verifyOpsForVersion(teal: List[TealComponent], version: int):
    """Verify that all TEAL operations are allowed in the specified version.

    Args:
        teal: Code to check.
        mode: The version to check against.

    Raises:
        TealInputError: if teal contains an operation not allowed in version.
    """
    for stmt in teal:
        if isinstance(stmt, TealOp):
            op = stmt.getOp()
            if op.min_version > version:
                raise TealInputError("Op not supported in TEAL version {}: {}. Minimum required version is {}".format(version, op, op.min_version))

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
                raise TealInputError("Op not supported in {} mode: {}".format(mode.name, op))

def compileTeal(ast: Expr, mode: Mode, *, version: int = DEFAULT_TEAL_VERSION) -> str:
    """Compile a PyTeal expression into TEAL assembly.

    Args:
        ast: The PyTeal expression to assemble.
        mode: The mode of the program to assemble. Must be Signature or Application.
        version (optional): The TEAL version used to assemble the program. This will determine which
            expressions and fields are able to be used in the program and how expressions compile to
            TEAL opcodes. Defaults to 2 if not included.

    Returns:
        A TEAL assembly program compiled from the input expression.

    Raises:
        TealInputError: if an operation in ast is not supported by the supplied mode and version.
    """
    if not (MIN_TEAL_VERSION <= version <= MAX_TEAL_VERSION) or type(version) != int:
        raise TealInputError("Unsupported TEAL version: {}. Excepted an integer in the range [{}, {}]".format(version, MIN_TEAL_VERSION, MAX_TEAL_VERSION))

    options = CompileOptions(mode=mode, version=version)

    start, _ = ast.__teal__(options)
    start.addIncoming()
    start.validateTree()

    start = TealBlock.NormalizeBlocks(start)
    start.validateTree()
    
    errors = start.validateSlots()
    if len(errors) > 0:
        msg = 'Encountered {} error{} during compilation'.format(len(errors), 's' if len(errors) != 1 else '')
        raise TealInternalError(msg) from errors[0]

    order = sortBlocks(start)
    teal = flattenBlocks(order)

    verifyOpsForVersion(teal, version)
    verifyOpsForMode(teal, mode)

    slots = set()
    for stmt in teal:
        for slot in stmt.getSlots():
            slots.add(slot)
    
    if len(slots) > NUM_SLOTS:
        # TODO: identify which slots can be reused
        raise TealInternalError("Too many slots in use: {}, maximum is {}".format(len(slots), NUM_SLOTS))
    
    for index, slot in enumerate(sorted(slots, key=lambda slot: slot.id)):
        for stmt in teal:
            stmt.assignSlot(slot, index)

    lines = ["#pragma version {}".format(version)]
    lines += [i.assemble() for i in teal]
    return "\n".join(lines)
