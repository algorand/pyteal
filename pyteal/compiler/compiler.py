from typing import List, Set

from ..ast import Expr, ScratchSlot
from ..ir import Mode, TealComponent, TealOp, TealBlock
from ..errors import TealInputError, TealInternalError
from ..config import NUM_SLOTS

from .sort import sortBlocks
from .flatten import flattenBlocks
from .constants import createConstantBlocks

MAX_TEAL_VERSION = 4
MIN_TEAL_VERSION = 2
DEFAULT_TEAL_VERSION = MIN_TEAL_VERSION


class CompileOptions:
    def __init__(
        self, *, mode: Mode = Mode.Signature, version: int = DEFAULT_TEAL_VERSION
    ):
        self.mode = mode
        self.version = version


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


def compileTeal(
    ast: Expr,
    mode: Mode,
    *,
    version: int = DEFAULT_TEAL_VERSION,
    assembleConstants: bool = False
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
    if not (MIN_TEAL_VERSION <= version <= MAX_TEAL_VERSION) or type(version) != int:
        raise TealInputError(
            "Unsupported TEAL version: {}. Excepted an integer in the range [{}, {}]".format(
                version, MIN_TEAL_VERSION, MAX_TEAL_VERSION
            )
        )

    options = CompileOptions(mode=mode, version=version)

    start, _ = ast.__teal__(options)
    start.addIncoming()
    start.validateTree()

    start = TealBlock.NormalizeBlocks(start)
    start.validateTree()

    errors = start.validateSlots()
    if len(errors) > 0:
        msg = "Encountered {} error{} during compilation".format(
            len(errors), "s" if len(errors) != 1 else ""
        )
        raise TealInternalError(msg) from errors[0]

    order = sortBlocks(start)
    teal = flattenBlocks(order)

    verifyOpsForVersion(teal, version)
    verifyOpsForMode(teal, mode)

    slots: Set[ScratchSlot] = set()
    slotIds: Set[int] = set()
    nextSlotIndex = 0
    for stmt in teal:
        for slot in stmt.getSlots():
            # If there are two unique slots with same IDs, raise an error
            if slot.id in slotIds and id(slot) not in [id(s) for s in slots]:
                raise TealInternalError(
                    "Slot ID {} has been assigned multiple times".format(slot.id)
                )
            slotIds.add(slot.id)
            slots.add(slot)

    if len(slots) > NUM_SLOTS:
        # TODO: identify which slots can be reused
        raise TealInternalError(
            "Too many slots in use: {}, maximum is {}".format(len(slots), NUM_SLOTS)
        )

    for slot in sorted(slots, key=lambda slot: slot.id):
        # Find next vacant slot that compiler can assign to
        while nextSlotIndex in slotIds:
            nextSlotIndex += 1
        for stmt in teal:
            if slot.isReservedSlot:
                # Slot ids under 256 are manually reserved slots
                stmt.assignSlot(slot, slot.id)
            else:
                stmt.assignSlot(slot, nextSlotIndex)
                slotIds.add(nextSlotIndex)

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
