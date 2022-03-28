from typing import List, cast, Set
from pyteal.ir.tealblock import TealBlock

from pyteal.ir.tealcomponent import TealComponent
from pyteal.ir.tealop import TealOp
from pyteal.ir.ops import Op


class OptimizeOptions:
    """An object which specifies the optimizations to be performed and relevant context.
    Args:

        scratch_slots (optional): cancel contiguous store/load operations
            that have no load dependencies elsewhere.
        skip_ids (optional): reserved slot ids that may be treated
            differently during optimization."""

    def __init__(self, *, scratch_slots: bool = False, skip_ids: Set[int] = None):
        self.scratch_slots = scratch_slots
        self.skip_ids: Set[int] = skip_ids if skip_ids is not None else set()


def _remove_extraneous_slot_access(start: TealBlock, remove: Set[int]):
    def keep_op(op: TealOp):
        if type(op) != TealOp or (op.op != Op.store and op.op != Op.load):
            return True

        return cast(int, op.args[0]) not in remove

    for block in TealBlock.Iterate(start):
        block.ops = list(filter(keep_op, block.ops))


def _has_load_dependencies(cur_block: TealBlock, start: TealBlock, slot: int, pos: int):
    for block in TealBlock.Iterate(start):
        for i, op in enumerate(block.ops):
            if block == cur_block and i == pos:
                continue

            if type(op) == TealOp and op.op == Op.load and op.args[0] == slot:
                return True

    return False


def _apply_slot_to_stack(cur_block: TealBlock, start: TealBlock, skip_ids: Set[int]):
    slots_to_remove = set()
    for i, op in enumerate(cur_block.ops[:-1]):
        if type(op) != TealOp or op.op != Op.store:
            continue

        # do not optimize away reserved and global slots
        if op.getSlots()[0].id in skip_ids:
            continue

        next_op = cur_block.ops[i + 1]
        if type(next_op) != TealOp or next_op.op != Op.load:
            continue

        if op.args[0] != next_op.args[0]:
            continue

        if not _has_load_dependencies(cur_block, start, cast(int, op.args[0]), i + 1):
            slots_to_remove.add(cast(int, op.args[0]))

    # print(str(slots_to_remove))
    _remove_extraneous_slot_access(start, slots_to_remove)


def apply_global_optimizations(start: TealBlock, options: OptimizeOptions) -> TealBlock:
    # limit number of iterations to length of teal program to avoid potential
    # infinite loops.
    for block in TealBlock.Iterate(start):
        prev_ops = block.ops.copy()
        for _ in range(len(block.ops)):
            if options.scratch_slots:
                _apply_slot_to_stack(block, start, options.skip_ids)

            if prev_ops == block.ops:
                break

    return start
