from typing import Tuple, List, Set, Dict, Optional, cast

from ..ast import ScratchSlot, SubroutineDefinition
from ..ir import Mode, TealComponent, TealBlock
from ..errors import TealInputError, TealInternalError
from ..config import NUM_SLOTS


def collectScratchSlots(
    subroutineMapping: Dict[Optional[SubroutineDefinition], List[TealComponent]]
) -> Dict[Optional[SubroutineDefinition], Set[ScratchSlot]]:
    """Find and return all referenced ScratchSlots for each subroutine.

    Args:
        subroutineMapping: A mapping from subroutine to the list of TealComponent which make up that
            subroutine. The key None is taken to mean the main program routine.

    Returns:
        A dictionary whose keys are the same as subroutineMapping, and whose values are sets of
        ScratchSlots referenced by each subroutine.
    """

    subroutineSlots: Dict[Optional[SubroutineDefinition], Set[ScratchSlot]] = dict()

    for subroutine, ops in subroutineMapping.items():
        slots: Set[ScratchSlot] = set()
        for stmt in ops:
            for slot in stmt.getSlots():
                slots.add(slot)
        subroutineSlots[subroutine] = slots

    return subroutineSlots


def assignScratchSlotsToSubroutines(
    subroutineMapping: Dict[Optional[SubroutineDefinition], List[TealComponent]],
    subroutineBlocks: Dict[Optional[SubroutineDefinition], TealBlock],
) -> Dict[Optional[SubroutineDefinition], Set[int]]:
    """Assign scratch slot values for an entire program.

    Args:
        subroutineMapping: A mapping from subroutine to the list of TealComponent which make up that
            subroutine. The key None is taken to mean the main program routine. The values of this
            map will be modified in order to assign specific slot values to all referenced scratch
            slots.

    Raises:
        TealInternalError: if the scratch slots referenced by the program do not fit into 256 slots,
            or if multiple ScratchSlots request the same slot ID.

    Returns:
        A dictionary whose keys are the same as subroutineMapping, and whose values are sets of
        integers representing the assigned IDs of slots which appear only in that subroutine
        (subroutine local slots).
    """
    subroutineSlots = collectScratchSlots(subroutineMapping)

    # all scratch slots referenced by the program
    allSlots: Set[ScratchSlot] = cast(Set[ScratchSlot], set()).union(
        *subroutineSlots.values()
    )

    # all scratch slots referenced by more than 1 subroutine
    globalSlots: Set[ScratchSlot] = set()

    # all scratch slots referenced by only 1 subroutine
    localSlots: Dict[Optional[SubroutineDefinition], Set[ScratchSlot]] = dict()

    for subroutine, slots in subroutineSlots.items():
        allOtherSlots: Set[ScratchSlot] = set()

        for otherSubroutine, otherSubroutineSlots in subroutineSlots.items():
            if subroutine is not otherSubroutine:
                allOtherSlots |= otherSubroutineSlots

        globalSlots |= slots & allOtherSlots
        localSlots[subroutine] = slots - globalSlots

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
        errors = start.validateSlots(slotsInUse=globalSlots)
        if len(errors) > 0:
            msg = "Encountered {} error{} when assigning slots to subroutine".format(
                len(errors), "s" if len(errors) != 1 else ""
            )
            raise TealInternalError(msg) from errors[0]

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

    for ops in subroutineMapping.values():
        for stmt in ops:
            for slot in stmt.getSlots():
                stmt.assignSlot(slot, slotAssignments[slot])

    assignedLocalSlots: Dict[Optional[SubroutineDefinition], Set[int]] = dict()
    for subroutine, slots in localSlots.items():
        assignedLocalSlots[subroutine] = set(slotAssignments[slot] for slot in slots)

    return assignedLocalSlots
