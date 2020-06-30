from typing import List

from .ast import Expr
from .ir import Mode, TealComponent, TealOp
from .errors import TealInputError, TealInternalError

NUM_SLOTS = 256

def verifyOpsForMode(teal: List[TealComponent], mode: Mode):
    for stmt in teal:
        if isinstance(stmt, TealOp):
            op = stmt.getOp()
            if not op.mode & mode:
                raise TealInputError("Op not supported in {} mode: {}".format(mode.name, op.value))

def compileTeal(ast: Expr, mode: Mode) -> str:
    """Compile a PyTeal expression into TEAL assembly.

    Args:
        ast: The PyTeal expression to assemble.

    Returns:
        str: A TEAL assembly program compiled from the input expression.
    """
    teal = ast.__teal__()

    verifyOpsForMode(teal, mode)

    slots = set()
    for stmt in teal:
        for slot in stmt.getSlots():
            slots.add(slot)
    
    if len(slots) > NUM_SLOTS:
        # TODO: identify which slots can be reused
        raise TealInternalError("Not yet implemented")
    
    location = 0
    while len(slots) > 0:
        slot = slots.pop()
        for stmt in teal:
            stmt.assignSlot(slot, location)
        location += 1

    lines = ["#pragma version 2"]
    lines += [i.assemble() for i in teal]
    return "\n".join(lines)
