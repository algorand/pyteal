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

    # All scratch slots referenced by the program, this is a set of ScratchSlot not scratch slot ids.
    # There may be equivalent scratch slots that have separate entries
    all_slots: Set[ScratchSlot] = global_slots | cast(Set[ScratchSlot], set()).union(
        *local_slots.values()
    )

    slot_assignments: dict[ScratchSlot, int] = dict()
    slot_ids: set[int] = set()

    # Get ids of the reserved slots, checking to make sure it hasnt been re-assigned
    for slot in all_slots:
        if not slot.isReservedSlot:
            continue

        # If there are two unique slots with same IDs, raise an error
        if slot.id in slot_ids:
            raise TealInternalError(
                "Slot ID {} has been assigned multiple times".format(slot.id)
            )
        slot_ids.add(slot.id)

    # Reassign local slots that arent used elsewhere, taking care not to
    # assign a slot that has been reserved
    for slots in local_slots.values():
        idx = 0
        local_reserved = set([slot.id for slot in slots if slot.isReservedSlot])
        for slot in slots:
            if slot.isReservedSlot:
                continue

            slot.id = idx
            idx += 1
            # If its reserved, we cant use it
            while slot.id in local_reserved:
                slot.id = idx
                idx += 1

    all_slot_ids: set[int] = set([s.id for s in all_slots])

    if len(all_slot_ids) > NUM_SLOTS:
        raise TealInternalError(
            "Too many slots in use: {}, maximum is {}".format(
                len(all_slot_ids), NUM_SLOTS
            )
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

    next_slot_index = 0
    for slot in sorted(all_slots, key=lambda slot: slot.id):
        # Find next vacant slot that compiler can assign to
        while next_slot_index in slot_ids:
            next_slot_index += 1

        if slot.isReservedSlot:
            # Slot ids under 256 are manually reserved slots
            slot_assignments[slot] = slot.id
        else:
            slot_assignments[slot] = next_slot_index
            slot_ids.add(next_slot_index)

    for start in subroutineBlocks.values():
        for block in TealBlock.Iterate(start):
            for op in block.ops:
                for slot in op.getSlots():
                    op.assignSlot(slot, slot_assignments[slot])

    assignedLocalSlots: Dict[Optional[SubroutineDefinition], Set[int]] = dict()
    for subroutine, slots in local_slots.items():
        assignedLocalSlots[subroutine] = set(slot_assignments[slot] for slot in slots)

    return assignedLocalSlots
