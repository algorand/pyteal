from dataclasses import dataclass
from typing import Dict, Final, List, Optional, Set, Tuple, cast

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
from pyteal.compiler.sourcemap import (
    _PyTealSourceMapper,
    PyTealSourceMap,
)
from pyteal.compiler.subroutines import (
    resolveSubroutines,
    spillLocalSlotsDuringRecursion,
)
from pyteal.errors import SourceMapDisabledError, TealInputError, TealInternalError
from pyteal.ir import (
    Mode,
    Op,
    TealBlock,
    TealComponent,
    TealOp,
    TealPragma,
    TealSimpleBlock,
)
from pyteal.stack_frame import NatalStackFrame, sourcemapping_off_context
from pyteal.types import TealType
from pyteal.util import algod_with_assertion


MAX_PROGRAM_VERSION = 10
FRAME_POINTERS_VERSION = 8
DEFAULT_SCRATCH_SLOT_OPTIMIZE_VERSION = 9
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
        optimize: Optional[OptimizeOptions] = None,
    ) -> None:
        self.mode: Final[Mode] = mode
        self.version: Final[int] = version
        self.optimize: Final[OptimizeOptions] = optimize or OptimizeOptions()
        self.use_frame_pointers: Final[bool] = self.optimize.use_frame_pointers(
            self.version
        )

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

    ret_expr: Optional[Expr] = None
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
    if currentSubroutine:
        decl = currentSubroutine.get_declaration_by_option(options.use_frame_pointers)
        if end.ops:
            end.ops[0]._sframes_container = decl

        if deferred_expr := decl.deferred_expr:
            # this represents code that should be inserted before each retsub op
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
            subroutine.get_declaration_by_option(options.use_frame_pointers),  # T2PT4
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


@dataclass(frozen=True)
class CompileResults:
    """Summary of compilation"""

    teal: str
    sourcemap: PyTealSourceMap | None = None


CompileResults.__module__ = "pyteal"


@dataclass
class _FullCompilationBundle:
    """
    Private class that groups together various artifacts required and produced by the compiler.

    The following artifacts should _NOT_ be returned to the user, as they could
    interfere with the compiler's idempotency. For example, keeping these
    artifacts around could make it difficult to guarantee that scratchslots
    are allocated as efficiently as possible, and assuming that such artifacts
    might continue existing after compilation interferes with the goal of making
    the compiler as reliable and efficient as possible:
    * teal_chunks
    * components

    NOTE: `annotated_teal` can grow quite large and become unsuitable for compilation as algod's compile
    endpoint may throw a "request body too large" error.
    Therefore, it is recommended that `teal` be used for algod compilation purposes.
    """

    ast: Expr
    mode: Mode
    version: int
    assemble_constants: bool
    optimize: Optional[OptimizeOptions]
    teal: str
    teal_chunks: list[str]
    components: list[TealComponent]
    sourcemapper: _PyTealSourceMapper | None = None
    annotated_teal: str | None = None

    def get_results(self) -> CompileResults:
        sourcemap: PyTealSourceMap | None = None
        if self.sourcemapper:
            sourcemap = self.sourcemapper.get_sourcemap(self.teal)

        return CompileResults(self.teal, sourcemap)


class Compilation:
    """
    A class that encapsulates the data needed to compile a PyTeal expression
    """

    def __init__(
        self,
        ast: Expr,
        mode: Mode,
        *,
        version: int = DEFAULT_PROGRAM_VERSION,
        assemble_constants: bool = False,
        assembly_type_track: bool = True,
        optimize: OptimizeOptions | None = None,
    ):
        """
        Instantiate a Compilation object providing the necessary data to compile a PyTeal expression.

        Args:
            ast: The PyTeal expression to assemble
            mode: The program's mode for execution. Either :any:`Mode.Signature` or :any:`Mode.Application`
            version (optional):  The program version used to assemble the program. This will determine which
                expressions and fields are able to be used in the program and how expressions compile to
                TEAL opcodes. Defaults to 2 if not included.
            assembleConstants (optional): When `True`, the compiler will produce a program with fully
                assembled constants, rather than using the pseudo-ops `int`, `byte`, and `addr`. These
                constants will be assembled in the most space-efficient way, so enabling this may reduce
                the compiled program's size. Enabling this option requires a minimum program version of 3.
                Defaults to `False`.
            assembly_type_track (optional): When `True`, the compiler will produce a program with type
                checking at assembly time (default behavior). When `False`, the compiler will turn off
                type checking at assembly time. This is only useful if PyTeal is producing incorrect
                TEAL code, or the assembler is producing incorrect type errors. Defaults to `True`.
            optimize (optional): `OptimizeOptions` that determine which optimizations will be applied.
        """
        self.ast = ast
        self.mode = mode
        self.version = version
        self.assemble_constants = assemble_constants
        self.assembly_type_track = assembly_type_track
        self.optimize: OptimizeOptions = optimize or OptimizeOptions()

    def compile(
        self,
        *,
        with_sourcemap: bool = False,
        teal_filename: str | None = None,
        pcs_in_sourcemap: bool = False,
        algod_client: AlgodClient | None = None,
        annotate_teal: bool = False,
        annotate_teal_headers: bool = False,
        annotate_teal_concise: bool = False,
    ) -> CompileResults:
        """Compile the PyTeal :code:`ast` to produce a TEAL program and other artifacts.

        Args:
            with_sourcemap (optional): When `True`, the compiler will produce a source map that associates
                each line of the generated TEAL program back to the original PyTeal source code. Defaults to `False`.
            teal_filename (optional): The filename to use in the sourcemap. Defaults to `None`.
            pcs_in_sourcemap (optional): When `True`, the compiler will include the program counter in
                relevant sourcemap artifacts. This requires an `AlgodClient` (see next param). Defaults to `False`.
            algod_client (optional): An `AlgodClient` to use to fetch program counters. Defaults to `None`.
                When `pcs_in_sourcemap` is `True` and `algod_client` is not provided, the compiler will
                assume that an Algorand Sandbox algod client is running on the default port (4001) and -if
                this is not the case- will raise an exception.
            annotate_teal (optional): When `True`, the compiler will produce a TEAL program with comments
                that describe the PyTeal source code that generated each line of the program. Defaults to `False`.
            annotate_teal_headers (optional): When `True` along with `annotate_teal` being `True`, a header
                line with column names will be added at the top of the annotated teal. Defaults to `False`.
            annotate_teal_concise (optional): When `True` along with `annotate_teal` being `True`, the compiler
                will provide fewer columns in the annotated teal. Defaults to `False`.

        Returns:
            A `CompileResults` object with the following data:
            * teal: the TEAL program
            * sourcemap (optional): if `with_sourcemap` is `True`, the following source map data is provided:
                * teal_filename (optional): the TEAL filename, if this was provided
                * r3_sourcemap: an `R3SourceMap` object that maps the generated TEAL program back to the original PyTeal source code and conforms to the specs of the `Source Map Revision 3 Proposal <https://sourcemaps.info/spec.html>`_
                * pc_sourcemap (optional): if `pcs_in_sourcemap` is `True`, a `PCSourceMap` object that maps the program counters assembled by the `AlgodClient` which was utilized in the compilation back to the TEAL program which was generated by the compiler. This conforms to the specs of the `Source Map Revision 3 Proposal <https://sourcemaps.info/spec.html>`_
                * annotated_teal (optional): if `annotate_teal` is `True`, the TEAL program with comments that describe the PyTeal source code that generated each line of the program

        Raises:
            TealInputError: if an operation in ast is not supported by the supplied mode and version.
            TealInternalError: if an internal error is encountered during compilation.
        """
        return self._compile_impl(
            with_sourcemap=with_sourcemap,
            teal_filename=teal_filename,
            pcs_in_sourcemap=pcs_in_sourcemap,
            algod_client=algod_client,
            annotate_teal=annotate_teal,
            annotate_teal_headers=annotate_teal_headers,
            annotate_teal_concise=annotate_teal_concise,
        ).get_results()

    def _compile_impl(
        self,
        with_sourcemap: bool = True,
        teal_filename: str | None = None,
        pcs_in_sourcemap: bool = False,
        algod_client: AlgodClient | None = None,
        annotate_teal: bool = False,
        annotate_teal_headers: bool = False,
        annotate_teal_concise: bool = True,
    ) -> _FullCompilationBundle:
        if (
            not (MIN_PROGRAM_VERSION <= self.version <= MAX_PROGRAM_VERSION)
            or type(self.version) is not int
        ):
            raise TealInputError(
                "Unsupported program version: {}. Excepted an integer in the range [{}, {}]".format(
                    self.version, MIN_PROGRAM_VERSION, MAX_PROGRAM_VERSION
                )
            )

        if with_sourcemap and NatalStackFrame.sourcemapping_is_off():
            raise SourceMapDisabledError()

        if annotate_teal and not with_sourcemap:
            raise ValueError(
                "In order annotate generated teal source, must set with_sourcemap True"
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
        if options.optimize.optimize_scratch_slots(self.version):
            options.optimize._skip_slots = collect_unoptimized_slots(
                subroutine_start_blocks
            )
            for start in subroutine_start_blocks.values():
                apply_global_optimizations(start, options.optimize, self.version)

        localSlotAssignments: Dict[
            Optional[SubroutineDefinition], Set[int]
        ] = assignScratchSlotsToSubroutines(subroutine_start_blocks)

        subroutineMapping: Dict[
            Optional[SubroutineDefinition], List[TealComponent]
        ] = sort_subroutine_blocks(subroutine_start_blocks, subroutine_end_blocks)

        spillLocalSlotsDuringRecursion(
            self.version, subroutineMapping, subroutineGraph, localSlotAssignments
        )

        subroutineLabels = resolveSubroutines(subroutineMapping)
        components: list[TealComponent] = flattenSubroutines(
            subroutineMapping, subroutineLabels, options
        )

        verifyOpsForVersion(components, options.version)
        verifyOpsForMode(components, options.mode)

        if self.assemble_constants:
            if self.version < 3:
                raise TealInternalError(
                    f"The minimum program version required to enable assembleConstants is 3. The current version is {self.version}."
                )
            components = createConstantBlocks(components)

        componentsPrefix: list[TealComponent] = [TealPragma(version=self.version)]
        if not self.assembly_type_track:
            componentsPrefix.append(TealPragma(type_track=False))

        components = componentsPrefix + components  # T2PT0
        teal_chunks = [tl.assemble() for tl in components]
        teal_code = "\n".join(teal_chunks)

        full_cpb = _FullCompilationBundle(
            ast=self.ast,
            mode=self.mode,
            version=self.version,
            assemble_constants=self.assemble_constants,
            optimize=self.optimize,
            teal=teal_code,
            teal_chunks=teal_chunks,
            components=components,
        )
        if not with_sourcemap:
            return full_cpb

        # Below is purely for the source mapper:

        source_mapper = _PyTealSourceMapper(
            teal_chunks=teal_chunks,
            components=components,
            build=True,
            teal_filename=teal_filename,
            include_pcs=pcs_in_sourcemap,
            algod=algod_client,
            annotate_teal=annotate_teal,
            annotate_teal_headers=annotate_teal_headers,
            annotate_teal_concise=annotate_teal_concise,
        )
        full_cpb.sourcemapper = source_mapper

        # run a second time without, and assert that the same teal is produced
        with sourcemapping_off_context():
            assert NatalStackFrame.sourcemapping_is_off()

            # implicitly recursive call!!
            teal_code_wo = compileTeal(
                self.ast,
                self.mode,
                version=self.version,
                assembleConstants=self.assemble_constants,
                optimize=self.optimize,
            )

            _PyTealSourceMapper._validate_teal_identical(
                teal_code_wo,
                teal_code,
                msg="FATAL ERROR. Program without sourcemaps (LEFT) differs from Program with (RIGHT)",
            )

        return full_cpb


Compilation.__module__ = "pyteal"


def compileTeal(
    ast: Expr,
    mode: Mode,
    *,
    version: int = DEFAULT_PROGRAM_VERSION,
    assembleConstants: bool = False,
    assembly_type_track: bool = True,
    optimize: OptimizeOptions | None = None,
) -> str:
    """Compile a PyTeal expression into TEAL assembly.

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
        assembly_type_track (optional): When `True`, the compiler will produce a program with type
            checking at assembly time (default behavior). When `False`, the compiler will turn off
            type checking at assembly time. This is only useful if PyTeal is producing incorrect
            TEAL code, or the assembler is producing incorrect type errors. Defaults to `True`.
        optimize (optional): OptimizeOptions that determine which optimizations will be applied.

    Returns:
        A TEAL assembly program compiled from the input expression.

    Raises:
        TealInputError: if an operation in ast is not supported by the supplied mode and version.
        TealInternalError: if an internal error is encountered during compilation.
    """
    bundle = Compilation(
        ast,
        mode,
        version=version,
        assemble_constants=assembleConstants,
        assembly_type_track=assembly_type_track,
        optimize=optimize,
    )._compile_impl(with_sourcemap=False)
    return bundle.teal
