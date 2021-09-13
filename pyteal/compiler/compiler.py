from typing import List, Tuple, Set, Dict, Optional, cast

from ..types import TealType
from ..ast import (
    Expr,
    Return,
    Seq,
    ScratchSlot,
    SubroutineDefinition,
    SubroutineDeclaration,
)
from ..ir import Mode, TealComponent, TealOp, TealBlock, TealSimpleBlock
from ..errors import TealInputError, TealInternalError

from .sort import sortBlocks
from .flatten import flattenBlocks, flattenSubroutines
from .scratchslots import assignScratchSlotsToSubroutines
from .subroutines import (
    findRecursionPoints,
    spillLocalSlotsDuringRecursion,
    resolveSubroutines,
)
from .constants import createConstantBlocks

MAX_TEAL_VERSION = 5
MIN_TEAL_VERSION = 2
DEFAULT_TEAL_VERSION = MIN_TEAL_VERSION


class CompileOptions:
    def __init__(
        self,
        *,
        mode: Mode = Mode.Signature,
        version: int = DEFAULT_TEAL_VERSION,
    ) -> None:
        self.mode = mode
        self.version = version

        self.currentSubroutine: Optional[SubroutineDefinition] = None

        self.breakBlocksStack: List[List[TealSimpleBlock]] = []
        self.continueBlocksStack: List[List[TealSimpleBlock]] = []

    def setSubroutine(self, subroutine: Optional[SubroutineDefinition]) -> None:
        self.currentSubroutine = subroutine

    def enterLoop(self) -> None:
        self.breakBlocksStack.append([])
        self.continueBlocksStack.append([])

    def isInLoop(self) -> bool:
        return len(self.breakBlocksStack) != 0

    def addLoopBreakBlock(self, block: TealSimpleBlock) -> None:
        if len(self.breakBlocksStack) == 0:
            raise TealInternalError("Cannot add break block when no loop is active")
        self.breakBlocksStack[-1].append(block)

    def addLoopContinueBlock(self, block: TealSimpleBlock) -> None:
        if len(self.continueBlocksStack) == 0:
            raise TealInternalError("Cannot add continue block when no loop is active")
        self.continueBlocksStack[-1].append(block)

    def exitLoop(self) -> Tuple[List[TealSimpleBlock], List[TealSimpleBlock]]:
        if len(self.breakBlocksStack) == 0 or len(self.continueBlocksStack) == 0:
            raise TealInternalError("Cannot exit loop when no loop is active")
        return (self.breakBlocksStack.pop(), self.continueBlocksStack.pop())


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
                raise TealInputError(
                    "Op not supported in TEAL version {}: {}. Minimum required version is {}".format(
                        version, op, op.min_version
                    )
                )


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
                raise TealInputError(
                    "Op not supported in {} mode: {}".format(mode.name, op)
                )


def compileSubroutine(
    ast: Expr,
    options: CompileOptions,
    subroutineMapping: Dict[Optional[SubroutineDefinition], List[TealComponent]],
    subroutineGraph: Dict[SubroutineDefinition, Set[SubroutineDefinition]],
    subroutineBlocks: Dict[Optional[SubroutineDefinition], TealBlock],
) -> None:
    currentSubroutine = (
        cast(SubroutineDeclaration, ast).subroutine
        if isinstance(ast, SubroutineDeclaration)
        else None
    )

    if not ast.has_return():
        if ast.type_of() == TealType.none:
            ast = Seq([ast, Return()])
        else:
            ast = Return(ast)

    options.setSubroutine(currentSubroutine)
    start, end = ast.__teal__(options)
    start.addIncoming()
    start.validateTree()

    start = TealBlock.NormalizeBlocks(start)
    start.validateTree()

    order = sortBlocks(start, end)
    teal = flattenBlocks(order)

    verifyOpsForVersion(teal, options.version)
    verifyOpsForMode(teal, options.mode)

    subroutineMapping[currentSubroutine] = teal
    subroutineBlocks[currentSubroutine] = start

    referencedSubroutines: Set[SubroutineDefinition] = set()
    for stmt in teal:
        for subroutine in stmt.getSubroutines():
            referencedSubroutines.add(subroutine)

    if currentSubroutine is not None:
        subroutineGraph[currentSubroutine] = referencedSubroutines

    newSubroutines = referencedSubroutines - subroutineMapping.keys()
    for subroutine in sorted(newSubroutines, key=lambda subroutine: subroutine.id):
        compileSubroutine(
            subroutine.getDeclaration(),
            options,
            subroutineMapping,
            subroutineGraph,
            subroutineBlocks,
        )


def compileTeal(
    ast: Expr,
    mode: Mode,
    *,
    version: int = DEFAULT_TEAL_VERSION,
    assembleConstants: bool = False,
) -> str:
    """Compile a PyTeal expression into TEAL assembly.

    Args:
        ast: The PyTeal expression to assemble.
        mode: The mode of the program to assemble. Must be Signature or Application.
        version (optional): The TEAL version used to assemble the program. This will determine which
            expressions and fields are able to be used in the program and how expressions compile to
            TEAL opcodes. Defaults to 2 if not included.
        assembleConstants (optional): When true, the compiler will produce a program with fully
            assembled constants, rather than using the pseudo-ops `int`, `byte`, and `addr`. These
            constants will be assembled in the most space-efficient way, so enabling this may reduce
            the compiled program's size. Enabling this option requires a minimum TEAL version of 3.
            Defaults to false.

    Returns:
        A TEAL assembly program compiled from the input expression.

    Raises:
        TealInputError: if an operation in ast is not supported by the supplied mode and version.
        TealInternalError: if an internal error is encounter during compilation.
    """
    if (
        not (MIN_TEAL_VERSION <= version <= MAX_TEAL_VERSION)
        or type(version) is not int
    ):
        raise TealInputError(
            "Unsupported TEAL version: {}. Excepted an integer in the range [{}, {}]".format(
                version, MIN_TEAL_VERSION, MAX_TEAL_VERSION
            )
        )

    options = CompileOptions(mode=mode, version=version)

    subroutineMapping: Dict[
        Optional[SubroutineDefinition], List[TealComponent]
    ] = dict()
    subroutineGraph: Dict[SubroutineDefinition, Set[SubroutineDefinition]] = dict()
    subroutineBlocks: Dict[Optional[SubroutineDefinition], TealBlock] = dict()
    compileSubroutine(
        ast, options, subroutineMapping, subroutineGraph, subroutineBlocks
    )

    localSlotAssignments = assignScratchSlotsToSubroutines(
        subroutineMapping, subroutineBlocks
    )

    spillLocalSlotsDuringRecursion(
        version, subroutineMapping, subroutineGraph, localSlotAssignments
    )

    subroutineLabels = resolveSubroutines(subroutineMapping)
    teal = flattenSubroutines(subroutineMapping, subroutineLabels)

    if assembleConstants:
        if version < 3:
            raise TealInternalError(
                "The minimum TEAL version required to enable assembleConstants is 3. The current version is {}".format(
                    version
                )
            )
        teal = createConstantBlocks(teal)

    lines = ["#pragma version {}".format(version)]
    lines += [i.assemble() for i in teal]
    return "\n".join(lines)
