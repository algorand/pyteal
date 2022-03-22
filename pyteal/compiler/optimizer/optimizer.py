from dataclasses import dataclass
from typing import List, cast

from pyteal.ir.tealcomponent import TealComponent
from pyteal.ir.tealop import TealOp
from pyteal.ir.ops import Op

@dataclass
class OptimizeOptions:
    """An object which specifies the optimizations to be performed.
    Args:
        useSlotToStack (optional): cancel contiguous store/load operations
            that have no load dependencies elsewhere.
        iterateOptimizations (optional): repeat the optimizations until the
            code is no longer changed."""

    use_slot_to_stack: bool = False
    iterate_optimizations: bool = False


def _has_load_dependencies(teal: List[TealComponent], slot: int, pos: int):
    for i, op in enumerate(teal):
        if i == pos:
            continue

        if type(op) == TealOp and op.op == Op.load and op.args[0] == slot:
            return True

    return False


def _apply_slot_to_stack(teal: List[TealComponent]) -> List[TealComponent]:
    remove = [False] * len(teal)
    for i, op in enumerate(teal[:-1]):
        if type(op) != TealOp or op.op != Op.store:
            continue

        next_op = teal[i + 1]
        if type(next_op) != TealOp or next_op.op != Op.load:
            continue

        if op.args[0] != next_op.args[0]:
            continue

        if not _has_load_dependencies(teal, cast(int, op.args[0]), i + 1):
            remove[i] = remove[i + 1] = True

    return [op for i, op in enumerate(teal) if not remove[i]]


def _apply_local_optimizations(
    teal: List[TealComponent], options: OptimizeOptions
) -> List[TealComponent]:
    # limit number of iterations to length of teal program to avoid potential
    # infinite loops.
    for _ in range(len(teal)):
        prev_teal = teal.copy()
        if options.use_slot_to_stack:
            teal = _apply_slot_to_stack(teal)

        if not options.iterate_optimizations or prev_teal == teal:
            break

    return teal


# Currently, only local optimizations are available so this is equivalent to
# calling applyLocalOptimizations().
def apply_optimizations(teal: List[TealComponent], options: OptimizeOptions):
    return _apply_local_optimizations(teal, options)
