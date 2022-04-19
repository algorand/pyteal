from typing import List, Tuple, Set, Dict, Optional, cast

from pyteal.compiler.optimizer import OptimizeOptions, apply_global_optimizations

from pyteal.types import TealType
from pyteal.ast import (
    Expr,
    Return,
    Seq,
    SubroutineDefinition,
    SubroutineDeclaration,
)
from pyteal.ir import Mode, TealComponent, TealOp, TealBlock, TealSimpleBlock
from pyteal.errors import TealInputError, TealInternalError

from pyteal.compiler.sort import sortBlocks
from pyteal.compiler.flatten import flattenBlocks, flattenSubroutines
from pyteal.compiler.scratchslots import (
    assignScratchSlotsToSubroutines,
    collect_unoptimized_slots,
)
from pyteal.compiler.subroutines import (
    spillLocalSlotsDuringRecursion,
    resolveSubroutines,
)
from pyteal.compiler.constants import createConstantBlocks

MAX_TEAL_VERSION = 6
MIN_TEAL_VERSION = 2
DEFAULT_TEAL_VERSION = MIN_TEAL_VERSION


class CompileOptions:
    def __init__(
        self,
        *,
        mode: Mode = Mode.Signature,
        version: int = DEFAULT_TEAL_VERSION,
        optimize: OptimizeOptions = None,
    ) -> None:
        self.mode = mode
        self.version = version
        self.optimize = optimize if optimize is not None else OptimizeOptions()

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
    subroutineGraph: Dict[SubroutineDefinition, Set[SubroutineDefinition]],
    subroutine_start_blocks: Dict[Optional[SubroutineDefinition], TealBlock],
    subroutine_end_blocks: Dict[Optional[SubroutineDefinition], TealBlock],
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

    subroutine_start_blocks[currentSubroutine] = start
    subroutine_end_blocks[currentSubroutine] = end

    referencedSubroutines: Set[SubroutineDefinition] = set()
    for stmt in teal:
        for subroutine in stmt.getSubroutines():
            referencedSubroutines.add(subroutine)

    if currentSubroutine is not None:
        subroutineGraph[currentSubroutine] = referencedSubroutines

    newSubroutines = referencedSubroutines - subroutine_start_blocks.keys()
    for subroutine in sorted(newSubroutines, key=lambda subroutine: subroutine.id):
        compileSubroutine(
            subroutine.getDeclaration(),
            options,
            subroutineGraph,
            subroutine_start_blocks,
            subroutine_end_blocks,
        )


def sort_subroutine_blocks(
    subroutine_start_blocks: Dict[Optional[SubroutineDefinition], TealBlock],
    subroutine_end_blocks: Dict[Optional[SubroutineDefinition], TealBlock],
) -> Dict[Optional[SubroutineDefinition], List[TealComponent]]:
    subroutine_mapping: Dict[
        Optional[SubroutineDefinition], List[TealComponent]
    ] = dict()
    for subroutine, start in subroutine_start_blocks.items():
        order = sortBlocks(start, subroutine_end_blocks[subroutine])
        subroutine_mapping[subroutine] = flattenBlocks(order)

    return subroutine_mapping


def compileTeal(
    ast: Expr,
    mode: Mode,
    *,
    version: int = DEFAULT_TEAL_VERSION,
    assembleConstants: bool = False,
    optimize: OptimizeOptions = None,
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
        optimize (optional): OptimizeOptions that determine which optimizations will be applied.

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

    options = CompileOptions(mode=mode, version=version, optimize=optimize)

    subroutineGraph: Dict[SubroutineDefinition, Set[SubroutineDefinition]] = dict()
    subroutine_start_blocks: Dict[Optional[SubroutineDefinition], TealBlock] = dict()
    subroutine_end_blocks: Dict[Optional[SubroutineDefinition], TealBlock] = dict()
    compileSubroutine(
        ast, options, subroutineGraph, subroutine_start_blocks, subroutine_end_blocks
    )

    # note: optimizations are off by default, in which case, apply_global_optimizations
    # won't make any changes. Because the optimizer is invoked on a subroutine's
    # control flow graph, the optimizer requires context across block boundaries. This
    # is necessary for the dependency checking of local slots. Global slots, slots
    # used by DynamicScratchVar, and reserved slots are not optimized.
    if options.optimize.scratch_slots:
        options.optimize._skip_slots = collect_unoptimized_slots(
            subroutine_start_blocks
        )
        for start in subroutine_start_blocks.values():
            apply_global_optimizations(start, options.optimize)

    localSlotAssignments = assignScratchSlotsToSubroutines(subroutine_start_blocks)

    subroutineMapping: Dict[
        Optional[SubroutineDefinition], List[TealComponent]
    ] = sort_subroutine_blocks(subroutine_start_blocks, subroutine_end_blocks)

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
