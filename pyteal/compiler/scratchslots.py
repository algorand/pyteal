from typing import Tuple, List, Set, Dict, Optional

from ..ast import ScratchSlot, SubroutineDefinition
from ..ir import Mode, TealComponent
from ..errors import TealInputError, TealInternalError
from ..config import NUM_SLOTS

def collectScratchSlots(subroutineMapping: Dict[Optional[SubroutineDefinition], List[TealComponent]]) -> Dict[Optional[SubroutineDefinition], Set[ScratchSlot]]:
    subroutineSlots: Dict[Optional[SubroutineDefinition], Set[ScratchSlot]] = dict()

    for subroutine, ops in subroutineMapping.items():
        slots: Set[ScratchSlot] = set()
        for stmt in ops:
            for slot in stmt.getSlots():
                slots.add(slot)
        subroutineSlots[subroutine] = slots

    return subroutineSlots

def assignScratchSlotsToSubroutines(subroutineMapping: Dict[Optional[SubroutineDefinition], List[TealComponent]]) -> Dict[Optional[SubroutineDefinition], Set[int]]:
    """Assign scratch slot values for an entire program.

    TODO: update this docstring

    Args:
        ops: a list of TealComponents that may contain unassigned ScratchSlot objects. This must
        represent the entire program being compiled.

    Raises:
        TealInternalError: if the scratch slots referenced by the program do not fit into 256 slots.

    Returns:
        A list of TealComponents whose scratch slots have been assigned to concrete values.
    """
    subroutineSlots = collectScratchSlots(subroutineMapping)

    # all scratch slots referenced by the program
    allSlots: Set[ScratchSlot] = set()
    for slots in subroutineSlots.values():
        allSlots |= slots
    
    # all scratch slots referenced by more than 1 subroutine
    globalSlots: Set[ScratchSlot] = set()
    for subroutine, slots in subroutineSlots.items():
        allOtherSlots: Set[ScratchSlot] = set()

        for otherSubroutine, otherSubroutineSlots in subroutineSlots.items():
            if subroutine != otherSubroutine:
                allOtherSlots |= otherSubroutineSlots
        
        globalSlots |= slots & allOtherSlots

    # all scratch slots referenced by only 1 subroutine
    localSlots: Dict[Optional[SubroutineDefinition], Set[ScratchSlot]] = dict()
    for subroutine, slots in subroutineSlots.items():
        localSlots[subroutine] = slots - globalSlots

    if len(allSlots) > NUM_SLOTS:
        # TODO: identify which slots can be reused
        # subroutines which never invoke each other can use the same slot ID for local slots
        raise TealInternalError("Too many slots in use: {}, maximum is {}".format(len(allSlots), NUM_SLOTS))
    
    slotAssignments: Dict[ScratchSlot, int] = dict()
    slotIds: Set[int] = set()
    
    for slot in allSlots:
        if not slot.isReservedSlot:
            continue

        # If there are two unique slots with same IDs, raise an error
        if slot.id in slotIds:
            raise TealInternalError("Slot ID {} has been assigned multiple times".format(slot.id))
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
