from typing import Set
from pyteal.ast import ScratchSlot
from pyteal.ir import TealBlock, TealOp, Op
from pyteal.errors import TealInternalError


class OptimizeOptions:
    """An object which specifies the optimizations to be performed and relevant context.

    _skip_slots: the slots that should be skipped during optimization. At the moment this includes:
            1. reserved slots because they may have dependencies outside
            the current application. For example, the 'gloads' opcode can
            access the slots of other applications in the tx group.
            2. global slots because they're outside the scope of global
            optimizations, which only apply to the control flow graph of
            a single subroutine.
            3. slots used with dynamic scratch vars. These slots use
            indirection by means of the 'stores' opcode and dependencies
            can only be determined at runtime.

    Args:

        scratch_slots (optional): cancel contiguous store/load operations
            that have no load dependencies elsewhere.
    """

    def __init__(self, *, scratch_slots: bool = False):
        self.scratch_slots = scratch_slots
        self._skip_slots: Set[ScratchSlot] = set()


def _remove_extraneous_slot_access(start: TealBlock, remove: Set[ScratchSlot]):
    def keep_op(op: TealOp) -> bool:
        if type(op) != TealOp or (op.op != Op.store and op.op != Op.load):
            return True

        return not set(op.getSlots()).issubset(remove)

    for block in TealBlock.Iterate(start):
        block.ops = list(filter(keep_op, block.ops))


# Very dumb, overly eager dependency checking. A "dependency" is considered
# any time the slot is loaded from in the entire control flow graph. This
# can definitely be improved in the future.
def _has_load_dependencies(
    cur_block: TealBlock, start: TealBlock, slot: ScratchSlot, pos: int
) -> bool:
    for block in TealBlock.Iterate(start):
        for i, op in enumerate(block.ops):
            if block == cur_block and i == pos:
                continue

            if type(op) == TealOp and op.op == Op.load and slot in set(op.getSlots()):
                return True

    return False


def _apply_slot_to_stack(
    cur_block: TealBlock, start: TealBlock, skip_slots: Set[ScratchSlot]
):
    slots_to_remove = set()
    # surprisingly, this slicing is totally safe - even if the list is empty.
    for i, op in enumerate(cur_block.ops[:-1]):
        if type(op) != TealOp or op.op != Op.store:
            continue

        if set(op.getSlots()).issubset(skip_slots):
            continue

        next_op = cur_block.ops[i + 1]
        if type(next_op) != TealOp or next_op.op != Op.load:
            continue

        cur_slots, next_slots = op.getSlots(), next_op.getSlots()
        if len(cur_slots) != 1 or len(next_slots) != 1:
            raise TealInternalError(
                "load/store op does not have exactly one slot argument"
            )
        if cur_slots[0] != next_slots[0]:
            continue

        if not _has_load_dependencies(cur_block, start, cur_slots[0], i + 1):
            slots_to_remove.add(cur_slots[0])

    _remove_extraneous_slot_access(start, slots_to_remove)


def apply_global_optimizations(start: TealBlock, options: OptimizeOptions) -> TealBlock:
    # limit number of iterations to length of teal program to avoid potential
    # infinite loops.
    for block in TealBlock.Iterate(start):
        for _ in range(len(block.ops)):
            prev_ops = block.ops.copy()
            if options.scratch_slots:
                _apply_slot_to_stack(block, start, options._skip_slots)

            if prev_ops == block.ops:
                break

    return start


OptimizeOptions.__module__ = "pyteal"
