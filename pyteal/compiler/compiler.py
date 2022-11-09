from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, cast

from algosdk.v2client.algod import AlgodClient

from pyteal.ast import Expr, Return, Seq, SubroutineDeclaration, SubroutineDefinition
from pyteal.compiler.constants import createConstantBlocks
from pyteal.compiler.flatten import flattenBlocks, flattenSubroutines
from pyteal.compiler.optimizer import OptimizeOptions, apply_global_optimizations
from pyteal.compiler.scratchslots import (
    assignScratchSlotsToSubroutines,
    collect_unoptimized_slots,
)
from pyteal.compiler.sort import sortBlocks
from pyteal.compiler.sourcemap import PyTealSourceMap, SourceMapDisabledError
from pyteal.compiler.subroutines import (
    resolveSubroutines,
    spillLocalSlotsDuringRecursion,
)
from pyteal.errors import TealInputError, TealInternalError
from pyteal.ir import (
    Mode,
    Op,
    TealBlock,
    TealComponent,
    TealOp,
    TealPragma,
    TealSimpleBlock,
)
from pyteal.stack_frame import Frames
from pyteal.types import TealType
from pyteal.util import algod_with_assertion

TComponents = TealComponent | TealPragma

MAX_PROGRAM_VERSION = 7
MIN_PROGRAM_VERSION = 2
DEFAULT_PROGRAM_VERSION = MIN_PROGRAM_VERSION


"""Deprecated. Use MAX_PROGRAM_VERSION instead."""
MAX_TEAL_VERSION = MAX_PROGRAM_VERSION
"""Deprecated. Use MIN_PROGRAM_VERSION instead."""
MIN_TEAL_VERSION = MIN_PROGRAM_VERSION
"""Deprecated. Use DEFAULT_PROGRAM_VERSION instead."""
DEFAULT_TEAL_VERSION = DEFAULT_PROGRAM_VERSION


class CompileOptions:
    def __init__(
        self,
        *,
        mode: Mode = Mode.Signature,
        version: int = DEFAULT_PROGRAM_VERSION,
        optimize: OptimizeOptions | None = None,
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
        return self.breakBlocksStack.pop(), self.continueBlocksStack.pop()


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
                    "Op not supported in program version {}: {}. Minimum required version is {}".format(
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
            ret_expr = Return()  # T2PT2
            ret_expr.trace = ast.trace
            seq_expr = Seq([ast, ret_expr])
            seq_expr.trace = ret_expr.trace
            ast = seq_expr
        else:
            ret_expr = Return(ast)  # T2PT3
            ret_expr.trace = ast.trace
            ast = ret_expr

    options.setSubroutine(currentSubroutine)

    start, end = ast.__teal__(options)
    start.addIncoming()
    start.validateTree()

    if (
        currentSubroutine is not None
        and currentSubroutine.get_declaration().deferred_expr is not None
    ):
        # this represents code that should be inserted before each retsub op
        deferred_expr = cast(Expr, currentSubroutine.get_declaration().deferred_expr)

        for block in TealBlock.Iterate(start):
            if not any(op.getOp() == Op.retsub for op in block.ops):
                continue

            if len(block.ops) != 1:
                # we expect all retsub ops to be in their own block at this point since
                # TealBlock.NormalizeBlocks has not yet been used
                raise TealInternalError(
                    f"Expected retsub to be the only op in the block, but there are {len(block.ops)} ops"
                )

            # we invoke __teal__ here and not outside of this loop because the same block cannot be
            # added in multiple places to the control flow graph
            deferred_start, deferred_end = deferred_expr.__teal__(options)
            deferred_start.addIncoming()
            deferred_start.validateTree()

            # insert deferred blocks between the previous block(s) and this one
            deferred_start.incoming = block.incoming
            block.incoming = [deferred_end]
            deferred_end.nextBlock = block

            for prev in deferred_start.incoming:
                prev.replaceOutgoing(block, deferred_start)

            if block is start:
                # this is the start block, replace start
                start = deferred_start

    start.validateTree()

    start = TealBlock.NormalizeBlocks(start)
    start.validateTree()

    subroutine_start_blocks[currentSubroutine] = start
    subroutine_end_blocks[currentSubroutine] = end

    referencedSubroutines: Set[SubroutineDefinition] = set()
    for block in TealBlock.Iterate(start):
        for stmt in block.ops:
            for subroutine in stmt.getSubroutines():
                referencedSubroutines.add(subroutine)

    if currentSubroutine is not None:
        subroutineGraph[currentSubroutine] = referencedSubroutines

    newSubroutines = referencedSubroutines - subroutine_start_blocks.keys()
    for subroutine in sorted(newSubroutines, key=lambda subroutine: subroutine.id):
        compileSubroutine(
            subroutine.get_declaration(),  # T2PT4
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


@dataclass
class CompilationBundle:
    ast: Expr
    mode: Mode
    version: int
    assemble_constants: bool
    optimize: OptimizeOptions | None
    teal: str
    lines: list[str]
    components: list[TealComponent]
    sourcemap: PyTealSourceMap | None = None


class Compilation:
    def __init__(
        self,
        ast: Expr,
        mode: Mode,
        *,
        version: int = DEFAULT_PROGRAM_VERSION,
        assemble_constants: bool = False,
        optimize: OptimizeOptions | None = None,
    ):
        self.ast = ast
        self.mode = mode
        self.version = version
        self.assemble_constants = assemble_constants
        self.optimize = optimize

    # TODO: API needs refactor....
    def compile(
        self,
        with_sourcemap: bool = True,
        teal_filename: str | None = None,
        pcs_in_sourcemap: bool = False,
        algod_client: AlgodClient | None = None,
        annotate_teal: bool = False,
        annotate_teal_headers: bool = False,
        annotate_teal_concise: bool = True,
        # deprecated:
        source_inference: bool = True,
        hybrid_source: bool = True,
    ) -> CompilationBundle:
        """Compile a PyTeal expression into TEAL assembly.

        TODO: this comment is out of date!!!

        Args:
            ast: The PyTeal expression to assemble.
            mode: The mode of the program to assemble. Must be Signature or Application.
            version (optional): The program version used to assemble the program. This will determine which
                expressions and fields are able to be used in the program and how expressions compile to
                TEAL opcodes. Defaults to 2 if not included.
            assembleConstants (optional): When true, the compiler will produce a program with fully
                assembled constants, rather than using the pseudo-ops `int`, `byte`, and `addr`. These
                constants will be assembled in the most space-efficient way, so enabling this may reduce
                the compiled program's size. Enabling this option requires a minimum program version of 3.
                Defaults to false.
            optimize (optional): OptimizeOptions that determine which optimizations will be applied.

        Returns:
            A TEAL assembly program compiled from the input expression.

        Raises:
            TealInputError: if an operation in ast is not supported by the supplied mode and version.
            TealInternalError: if an internal error is encounter during compilation.
        """
        if (
            not (MIN_PROGRAM_VERSION <= self.version <= MAX_PROGRAM_VERSION)
            or type(self.version) is not int
        ):
            raise TealInputError(
                "Unsupported program version: {}. Excepted an integer in the range [{}, {}]".format(
                    self.version, MIN_PROGRAM_VERSION, MAX_PROGRAM_VERSION
                )
            )

        if with_sourcemap and Frames.skipping_all():
            raise SourceMapDisabledError()

        if annotate_teal and not with_sourcemap:
            raise ValueError(
                "In order annotate generated teal source, must set source_inference True"
            )

        if pcs_in_sourcemap:
            # bootstrap an algod_client if not provided, and in either case, run a healthcheck
            algod_client = algod_with_assertion(
                algod_client, msg="Adding PC's to sourcemap requires live Algod"
            )

        options = CompileOptions(
            mode=self.mode, version=self.version, optimize=self.optimize
        )

        subroutineGraph: Dict[SubroutineDefinition, Set[SubroutineDefinition]] = dict()
        subroutine_start_blocks: Dict[
            Optional[SubroutineDefinition], TealBlock
        ] = dict()
        subroutine_end_blocks: Dict[Optional[SubroutineDefinition], TealBlock] = dict()
        compileSubroutine(
            self.ast,
            options,
            subroutineGraph,
            subroutine_start_blocks,
            subroutine_end_blocks,
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
            self.version, subroutineMapping, subroutineGraph, localSlotAssignments
        )

        subroutineLabels = resolveSubroutines(subroutineMapping)
        components: list[TComponents] = flattenSubroutines(
            subroutineMapping, subroutineLabels
        )

        verifyOpsForVersion(components, options.version)
        verifyOpsForMode(components, options.mode)

        if self.assemble_constants:
            if self.version < 3:
                raise TealInternalError(
                    "The minimum program version required to enable assembleConstants is 3. The current version is {}".format(
                        self.version
                    )
                )
            components = createConstantBlocks(components)

        components = [cast(TComponents, TealPragma(self.version))] + components  # T2PT0
        lines = [tl.assemble() for tl in components]
        teal_code = "\n".join(lines)

        cpb = CompilationBundle(
            ast=self.ast,
            mode=self.mode,
            version=self.version,
            assemble_constants=self.assemble_constants,
            optimize=self.optimize,
            teal=teal_code,
            lines=lines,
            components=components,
        )
        if not with_sourcemap:
            return cpb

        cpb.sourcemap = PyTealSourceMap(
            compiled_teal_lines=lines,
            components=components,
            build=True,
            teal_file=teal_filename,
            include_pcs=pcs_in_sourcemap,
            algod=algod_client,
            annotate_teal=annotate_teal,
            # deprecated:
            source_inference=source_inference,
            hybrid=hybrid_source,
        )

        if annotate_teal:
            cpb.teal = cpb.sourcemap.annotated_teal(
                omit_headers=not annotate_teal_headers, concise=annotate_teal_concise
            )

        return cpb


def compileTeal(
    ast: Expr,
    mode: Mode,
    *,
    version: int = DEFAULT_PROGRAM_VERSION,
    assembleConstants: bool = False,
    optimize: OptimizeOptions | None = None,
) -> str:
    bundle = Compilation(
        ast,
        mode,
        version=version,
        assemble_constants=assembleConstants,
        optimize=optimize,
    ).compile(with_sourcemap=False)
    return bundle.teal
