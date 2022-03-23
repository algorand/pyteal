from dataclasses import dataclass
from typing import List, cast, Set

from pyteal.ir.tealcomponent import TealComponent
from pyteal.ir.tealop import TealOp
from pyteal.ir.ops import Op


class OptimizeOptions:
    """An object which specifies the optimizations to be performed and relevant context.
    Args:

        scratch_slots (optional): cancel contiguous store/load operations
            that have no load dependencies elsewhere.
        reserved_ids (optional): reserved slot ids that may be treated
            differently during optimization."""

    def __init__(self, *, scratch_slots: bool = False, reserved_ids: Set[int] = None):
        self.scratch_slots = scratch_slots
        self.reserved_ids = reserved_ids if reserved_ids is not None else set()


def _has_load_dependencies(teal: List[TealComponent], slot: int, pos: int):
    for i, op in enumerate(teal):
        if i == pos:
            continue

        if type(op) == TealOp and op.op == Op.load and op.args[0] == slot:
            return True

    return False


def _apply_slot_to_stack(
    teal: List[TealComponent], reserved_ids: Set[int]
) -> List[TealComponent]:
    remove = set()
    for i, op in enumerate(teal[:-1]):
        if type(op) != TealOp or op.op != Op.store:
            continue

        # do not optimize away reserved slots
        if cast(int, op.args[0]) in reserved_ids:
            continue

        next_op = teal[i + 1]
        if type(next_op) != TealOp or next_op.op != Op.load:
            continue

        if op.args[0] != next_op.args[0]:
            continue

        if not _has_load_dependencies(teal, cast(int, op.args[0]), i + 1):
            remove.update([i, i + 1])

    return [op for i, op in enumerate(teal) if i not in remove]


def _apply_local_optimizations(
    teal: List[TealComponent], options: OptimizeOptions
) -> List[TealComponent]:
    # limit number of iterations to length of teal program to avoid potential
    # infinite loops.
    for _ in range(len(teal)):
        prev_teal = teal.copy()
        if options.scratch_slots:
            teal = _apply_slot_to_stack(teal, options.reserved_ids)

        if prev_teal == teal:
            break

    return teal


# Currently, only local optimizations are available so this is equivalent to
# calling apply_local_optimizations().
def apply_optimizations(
    teal: List[TealComponent], options: OptimizeOptions
) -> List[TealComponent]:
    return _apply_local_optimizations(teal, options)
