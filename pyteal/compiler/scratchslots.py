from typing import Tuple, Set, Dict, Optional, cast

from pyteal.ast import ScratchSlot, SubroutineDefinition
from pyteal.ir import TealBlock, Op
from pyteal.errors import TealInternalError
from pyteal.config import NUM_SLOTS


def collect_unoptimized_slots(
    subroutineBlocks: Dict[Optional[SubroutineDefinition], TealBlock]
) -> Set[ScratchSlot]:
    """Find and return all referenced ScratchSlots that need to be skipped
    during optimization.

    Args:
        subroutineBlocks: A mapping from subroutine to the subroutine's control flow graph.
        The key None is taken to mean the main program routine.

    Returns:
        A set which contains the slots used by DynamicScratchVars, all the reserved slots,
            and all global slots.
    """

    unoptimized_slots: Set[ScratchSlot] = set()

    def collectSlotsFromBlock(block: TealBlock):
        for op in block.ops:
            for slot in op.getSlots():
                # dynamic slot or reserved slot
                if op.op == Op.int or slot.isReservedSlot:
                    unoptimized_slots.add(slot)

    for _, start in subroutineBlocks.items():
        for block in TealBlock.Iterate(start):
            collectSlotsFromBlock(block)

    global_slots, _ = collectScratchSlots(subroutineBlocks)
    unoptimized_slots.update(global_slots)
    return unoptimized_slots


def collectScratchSlots(
    subroutineBlocks: Dict[Optional[SubroutineDefinition], TealBlock]
) -> Tuple[Set[ScratchSlot], Dict[Optional[SubroutineDefinition], Set[ScratchSlot]]]:
    """Find and return all referenced ScratchSlots for each subroutine.

    Args:
        subroutineBlocks: A mapping from subroutine to the subroutine's control flow graph.
        The key None is taken to mean the main program routine.

    Returns:
        A tuple of a set containing all global slots and a dictionary whose keys are the
            same as subroutineBlocks, and whose values are the local slots of that
            subroutine.
    """

    subroutineSlots: Dict[Optional[SubroutineDefinition], Set[ScratchSlot]] = dict()

    def collectSlotsFromBlock(block: TealBlock, slots: Set[ScratchSlot]):
        for op in block.ops:
            for slot in op.getSlots():
                slots.add(slot)

    for subroutine, start in subroutineBlocks.items():
        slots: Set[ScratchSlot] = set()
        for block in TealBlock.Iterate(start):
            collectSlotsFromBlock(block, slots)

        subroutineSlots[subroutine] = slots

    # all scratch slots referenced by more than 1 subroutine
    global_slots: Set[ScratchSlot] = set()

    # all scratch slots referenced by only 1 subroutine
    local_slots: Dict[Optional[SubroutineDefinition], Set[ScratchSlot]] = dict()

    for subroutine, slots in subroutineSlots.items():
        allOtherSlots: Set[ScratchSlot] = set()

        for otherSubroutine, otherSubroutineSlots in subroutineSlots.items():
            if subroutine is not otherSubroutine:
                allOtherSlots |= otherSubroutineSlots

        global_slots |= slots & allOtherSlots
        local_slots[subroutine] = slots - global_slots

    return global_slots, local_slots


def assignScratchSlotsToSubroutines(
    subroutineBlocks: Dict[Optional[SubroutineDefinition], TealBlock],
) -> Dict[Optional[SubroutineDefinition], Set[int]]:
    """Assign scratch slot values for an entire program.

    Args:
        subroutineBlocks: A mapping from subroutine to the control flow graph of the subroutine's
            blocks. The key None is taken to mean the main program routine. The values of this
            map will be modified in order to assign specific slot values to all referenced scratch
            slots.

    Raises:
        TealInternalError: if the scratch slots referenced by the program do not fit into 256 slots,
            or if multiple ScratchSlots request the same slot ID.

    Returns:
        A dictionary whose keys are the same as subroutineBlocks, and whose values are sets of
        integers representing the assigned IDs of slots which appear only in that subroutine
        (subroutine local slots).
    """
    global_slots, local_slots = collectScratchSlots(subroutineBlocks)
    # all scratch slots referenced by the program
    allSlots: Set[ScratchSlot] = global_slots | cast(Set[ScratchSlot], set()).union(
        *local_slots.values()
    )

    slotAssignments: Dict[ScratchSlot, int] = dict()
    slotIds: Set[int] = set()

    for slot in allSlots:
        if not slot.isReservedSlot:
            continue

        # If there are two unique slots with same IDs, raise an error
        if slot.id in slotIds:
            raise TealInternalError(
                "Slot ID {} has been assigned multiple times".format(slot.id)
            )
        slotIds.add(slot.id)

    if len(allSlots) > NUM_SLOTS:
        # TODO: identify which slots can be reused
        # subroutines which never invoke each other can use the same slot ID for local slots
        raise TealInternalError(
            "Too many slots in use: {}, maximum is {}".format(len(allSlots), NUM_SLOTS)
        )

    # verify that all local slots are assigned to before being loaded.
    # TODO: for simplicity, the current implementation does not perform this check with global slots
    # as well, but that would be a good improvement
    for subroutine, start in subroutineBlocks.items():
        errors = start.validateSlots(slotsInUse=global_slots)
        if len(errors) > 0:
            msg = "Encountered {} error{} when assigning slots to subroutine".format(
                len(errors), "s" if len(errors) != 1 else ""
            )
            raise TealInternalError(msg) from errors[0]

    nextSlotIndex = 0
    for slot in sorted(allSlots, key=lambda slot: slot.id):
        # Find next vacant slot that compiler can assign to
        while nextSlotIndex in slotIds:
            nextSlotIndex += 1

        if slot.isReservedSlot:
            # Slot ids under 256 are manually reserved slots
            slotAssignments[slot] = slot.id
        else:
            slotAssignments[slot] = nextSlotIndex
            slotIds.add(nextSlotIndex)

    for start in subroutineBlocks.values():
        for block in TealBlock.Iterate(start):
            for op in block.ops:
                for slot in op.getSlots():
                    op.assignSlot(slot, slotAssignments[slot])

    assignedLocalSlots: Dict[Optional[SubroutineDefinition], Set[int]] = dict()
    for subroutine, slots in local_slots.items():
        assignedLocalSlots[subroutine] = set(slotAssignments[slot] for slot in slots)

    return assignedLocalSlots
