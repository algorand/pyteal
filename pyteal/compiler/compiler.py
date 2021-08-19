from typing import List, Set, Dict, Optional, cast

from ..types import TealType
from ..ast import Expr, Return, Seq, ScratchSlot, SubroutineDefinition, SubroutineDeclaration
from ..ir import Mode, TealComponent, TealOp, TealBlock
from ..errors import TealInputError, TealInternalError

from .sort import sortBlocks
from .flatten import flattenBlocks, flattenSubroutines
from .scratchslots import assignScratchSlotsToSubroutines
from .subroutines import findRecursionPoints, spillLocalSlotsDuringRecursion, resolveSubroutines
from .constants import createConstantBlocks

MAX_TEAL_VERSION = 4
MIN_TEAL_VERSION = 2
DEFAULT_TEAL_VERSION = MIN_TEAL_VERSION

class CompileOptions:

    def __init__(self, *, mode: Mode = Mode.Signature, version: int = DEFAULT_TEAL_VERSION, currentSubroutine: SubroutineDefinition = None):
        self.mode = mode
        self.version = version
        self.currentSubroutine = currentSubroutine

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

def compileSubroutine(ast: Expr, options: CompileOptions, subroutineMapping: Dict[Optional[SubroutineDefinition], List[TealComponent]], subroutineGraph: Dict[SubroutineDefinition, Set[SubroutineDefinition]]) -> None:
    currentSubroutine = cast(SubroutineDeclaration, ast).subroutine if isinstance(ast, SubroutineDeclaration) else None

    if not ast.has_return():
        if ast.type_of() == TealType.none:
            ast = Seq([ast, Return()])
        else:
            ast = Return(ast)

    options.currentSubroutine = currentSubroutine
    start, _ = ast.__teal__(options)
    start.addIncoming()
    start.validateTree()

    start = TealBlock.NormalizeBlocks(start)
    start.validateTree()
    
    # TODO: this probably needs to get modified since scratch slots may span multiple subroutines
    # errors = start.validateSlots()
    # if len(errors) > 0:
    #     msg = 'Encountered {} error{} during compilation'.format(len(errors), 's' if len(errors) != 1 else '')
    #     raise TealInternalError(msg) from errors[0]

    order = sortBlocks(start)
    teal = flattenBlocks(order)

    verifyOpsForVersion(teal, options.version)
    verifyOpsForMode(teal, options.mode)

    subroutineMapping[currentSubroutine] = teal

    referencedSubroutines: Set[SubroutineDefinition] = set()
    for stmt in teal:
        for subroutine in stmt.getSubroutines():
            referencedSubroutines.add(subroutine)
    
    if currentSubroutine is not None:
        subroutineGraph[currentSubroutine] = referencedSubroutines

    newSubroutines = referencedSubroutines - subroutineMapping.keys()
    for subroutine in sorted(newSubroutines, key=lambda subroutine: subroutine.id):
        compileSubroutine(subroutine.getDeclaration(), options, subroutineMapping, subroutineGraph)

def compileTeal(ast: Expr, mode: Mode, *, version: int = DEFAULT_TEAL_VERSION, assembleConstants: bool = False) -> str:
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
    if not (MIN_TEAL_VERSION <= version <= MAX_TEAL_VERSION) or type(version) != int:
        raise TealInputError("Unsupported TEAL version: {}. Excepted an integer in the range [{}, {}]".format(version, MIN_TEAL_VERSION, MAX_TEAL_VERSION))

    options = CompileOptions(mode=mode, version=version)

    subroutineMapping: Dict[Optional[SubroutineDefinition], List[TealComponent]] = dict()
    subroutineGraph: Dict[SubroutineDefinition, Set[SubroutineDefinition]] = dict()
    compileSubroutine(ast, options, subroutineMapping, subroutineGraph)

    localSlotAssignments = assignScratchSlotsToSubroutines(subroutineMapping)

    recursivePoints = findRecursionPoints(subroutineGraph)
    spillLocalSlotsDuringRecursion(subroutineMapping, recursivePoints, localSlotAssignments)

    subroutineLabels = resolveSubroutines(subroutineMapping)
    teal = flattenSubroutines(subroutineMapping, subroutineLabels)

    if assembleConstants:
        if version < 3:
            raise TealInternalError("The minimum TEAL version required to enable assembleConstants is 3. The current version is {}".format(version))
        teal = createConstantBlocks(teal)

    lines = ["#pragma version {}".format(version)]
    lines += [i.assemble() for i in teal]
    return "\n".join(lines)
