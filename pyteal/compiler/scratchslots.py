from typing import Tuple, Set, Dict, Optional, cast

from pyteal.ast import ScratchSlot, SubroutineDefinition
from pyteal.ir import TealBlock, Op
from pyteal.errors import TealInternalError
from pyteal.config import NUM_SLOTS
from pyteal.compiler.subroutines import find_callstack_exclusive_subroutines


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


def combine_subroutine_slot_assignments_greedy_algorithm(
    combined_subroutine_groups: list[set[Optional[SubroutineDefinition]]],
    subroutine_graph: dict[Optional[SubroutineDefinition], set[SubroutineDefinition]],
) -> None:
    """This is an imperfect greedy algorithm to share scratch slot assignments between callstack
    exclusive subroutines.

    * It's granularity is at the subroutine level, meaning it decides that two subroutines must share
      all of their scratch slot assignments, or none of them.
    * It uses the "exclusivity" of a subroutine (i.e. how many other subroutines it's callstack
      exclusive with) as a heuristic to combine subroutines.
    * Analysis has not been done to prove that this algorithm always terminates (or if its results
      are anywhere near optimal).
    * WARNING: this algorithm DOES NOT honor user-defined scratch slots. Those slots may be
      assigned to a numeric slot which IS NOT what the user specified.

    Args:
        combined_subroutine_groups: A list of sets of subroutines. Each set indicates subroutines
            which will share scratch slot assignments. This is a makeshift union-find data
            structure.
        subroutine_graph: A graph of subroutines. Each key is a subroutine (the main routine should
            not be present), which represents a node in the graph. Each value is a set of all
            subroutines that specific subroutine calls, which represent directional edges in the
            graph.
    """
    callstack_exclusive_subroutines = find_callstack_exclusive_subroutines(
        subroutine_graph
    )

    if len(callstack_exclusive_subroutines) == 0:
        return

    # choose "most exclusive" (i.e. most compatible) subroutine to start
    current_subroutine = max(
        callstack_exclusive_subroutines.keys(),
        key=lambda s: len(callstack_exclusive_subroutines[s]),
    )
    while True:
        group_index = -1
        for i, group in enumerate(combined_subroutine_groups):
            if current_subroutine in group:
                group_index = i
                break

        # only look at subroutines we're not already grouped with
        new_callstack_exclusive = [
            s
            for s in callstack_exclusive_subroutines[current_subroutine]
            if s not in combined_subroutine_groups[group_index]
        ]
        if len(new_callstack_exclusive) == 0:
            # nothing else to do
            break

        # choose the "most exclusive" subroutine that is exclusive to `current_subroutine`
        to_combine = max(
            new_callstack_exclusive,
            key=lambda s: len(callstack_exclusive_subroutines[s]),
        )
        # Share scratch slot assignments between `current_subroutine` and `to_combine`.
        to_combine_group_index = -1
        for i, group in enumerate(combined_subroutine_groups):
            if to_combine in group:
                to_combine_group_index = i
                break
        combined_subroutine_groups[group_index] |= combined_subroutine_groups[
            to_combine_group_index
        ]
        combined_subroutine_groups.pop(to_combine_group_index)

        # BEWARE! Now that we've decided to share scratch slot assignments between the two
        # subroutines, this potentially limits the other subroutines that they can share assignments
        # with. Specifically, if even if `current_subroutine` is callstack exclusive with another
        # subroutine `X`, if `to_combine` is not callstack exclusive with `X`, it's no longer safe
        # for `current_subroutine` to share assignments with `X`. We encode this constraint by
        # taking the intersection of `current_subroutine` and `to_combine`'s callstack exclusive
        # subroutines.
        intersection = (
            callstack_exclusive_subroutines[current_subroutine]
            & callstack_exclusive_subroutines[to_combine]
        )
        callstack_exclusive_subroutines[current_subroutine] = intersection | {
            to_combine
        }
        callstack_exclusive_subroutines[to_combine] = intersection | {
            cast(SubroutineDefinition, current_subroutine)
        }

        current_subroutine = max(
            callstack_exclusive_subroutines.keys(),
            key=lambda s: len(callstack_exclusive_subroutines[s]),
        )


def assignScratchSlotsToSubroutines(
    subroutineBlocks: Dict[Optional[SubroutineDefinition], TealBlock],
    subroutine_graph: dict[Optional[SubroutineDefinition], set[SubroutineDefinition]],
) -> Dict[Optional[SubroutineDefinition], Set[int]]:
    """Assign scratch slot values for an entire program.

    Args:
        subroutineBlocks: A mapping from subroutine to the control flow graph of the subroutine's
            blocks. The key None is taken to mean the main program routine. The values of this
            map will be modified in order to assign specific slot values to all referenced scratch
            slots.
        subroutine_graph: A graph of subroutines. Each key is a subroutine (the main routine should
            not be present), which represents a node in the graph. Each value is a set of all
            subroutines that specific subroutine calls, which represent directional edges in the
            graph.

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

    # combined_subroutine_groups is a makeshift union-find data structure which identifies which
    # subroutines will share scratch slot assignments.
    # TODO: replace this with an actual union-find data structure
    # TODO: it may make more sense to decide whether two subroutines can share an assignment on a
    # slot-by-slot basis, instead of grouping all a subroutine's slots together.
    combined_subroutine_groups: list[set[Optional[SubroutineDefinition]]] = [
        {s} for s in subroutine_graph.keys()
    ]

    # TODO: implement a way to opt into this optimization -- don't always run it
    combine_subroutine_slot_assignments_greedy_algorithm(
        combined_subroutine_groups, subroutine_graph
    )

    # the "spokesperson" for a group is the subroutine with the largest number of local slots
    combined_subroutine_groups_spokesperson: list[Optional[SubroutineDefinition]] = []
    # all other subroutines in the group will have their local slots mapped to their spokesperson's
    local_slot_mappings_to_spokesperson: list[dict[ScratchSlot, ScratchSlot]] = []
    for group in combined_subroutine_groups:
        spokesperson = max(group, key=lambda s: len(local_slots[s]))
        spokesperson_local_slots = list(local_slots[spokesperson])
        local_slot_mappings = {slot: slot for slot in spokesperson_local_slots}

        for subroutine in group:
            if subroutine is spokesperson:
                continue
            for i, slot in enumerate(local_slots[subroutine]):
                local_slot_mappings[slot] = spokesperson_local_slots[i]

        combined_subroutine_groups_spokesperson.append(spokesperson)
        local_slot_mappings_to_spokesperson.append(local_slot_mappings)

    slots_to_assign: set[ScratchSlot] = global_slots | cast(
        set[ScratchSlot], set()
    ).union(
        *[
            local_slots[spokesperson]
            for spokesperson in combined_subroutine_groups_spokesperson
        ]
    )

    if len(slots_to_assign) > NUM_SLOTS:
        raise TealInternalError(
            "Too many slots in use: {}, maximum is {}".format(
                len(slots_to_assign), NUM_SLOTS
            )
        )

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

    # Run the above check on all slots (before subroutine combination optimization), but clear it out
    # and populate slotIds again. We only do this because the optimization algorithm above doesn't
    # honor user-defined slot IDs.
    slotIds.clear()

    for slot in slots_to_assign:
        if not slot.isReservedSlot:
            continue
        slotIds.add(slot.id)

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

    slotAssignments: Dict[ScratchSlot, int] = dict()
    nextSlotIndex = 0
    for slot in sorted(slots_to_assign, key=lambda slot: slot.id):
        # Find next vacant slot that compiler can assign to
        while nextSlotIndex in slotIds:
            nextSlotIndex += 1

        if slot.isReservedSlot:
            # Slot ids under 256 are manually reserved slots
            slotAssignments[slot] = slot.id
        else:
            slotAssignments[slot] = nextSlotIndex
            slotIds.add(nextSlotIndex)

    for subroutine, start in subroutineBlocks.items():
        group_index = -1
        for i, group in enumerate(combined_subroutine_groups):
            if subroutine in group:
                group_index = i
                break
        assert group_index != -1

        slot_mapping = local_slot_mappings_to_spokesperson[group_index]

        for block in TealBlock.Iterate(start):
            for op in block.ops:
                for slot in op.getSlots():
                    if slot in slot_mapping:
                        # a local slot
                        op.assignSlot(slot, slotAssignments[slot_mapping[slot]])
                    else:
                        # a global slot
                        op.assignSlot(slot, slotAssignments[slot])

    assignedLocalSlots: Dict[Optional[SubroutineDefinition], Set[int]] = dict()
    for i, group in enumerate(combined_subroutine_groups):
        slot_mapping = local_slot_mappings_to_spokesperson[i]
        for subroutine in group:
            assignedLocalSlots[subroutine] = set(
                slotAssignments[slot_mapping[slot]] for slot in local_slots[subroutine]
            )

    return assignedLocalSlots
