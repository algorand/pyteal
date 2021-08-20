from typing import List

from ..ir import TealBlock, TealSimpleBlock, TealConditionalBlock
from ..errors import TealInternalError


def sortBlocks(start: TealBlock, end: TealBlock) -> List[TealBlock]:
    """Topologically sort the graph which starts with the input TealBlock.

    Args:
        start: The starting point of the graph to sort.

    Returns:
        An ordered list of TealBlocks that is sorted such that every block is guaranteed to appear
        in the list before all of its outgoing blocks.
    """
    S = [start]
    order = []
    visited = set()  # I changed visited to a set to be more efficient
    while len(S) != 0:
        n = S.pop()

        if id(n) in visited:
            continue

        S += n.getOutgoing()

        order.append(n)
        visited.add(id(n))

    endIndex = -1
    for i, block in enumerate(order):
        if block == end:
            endIndex = i
            break

    if endIndex == -1:
        raise TealInternalError("End block not present")

    order.pop(endIndex)
    order.append(end)

    return order

    # S = [start]
    # order = []
    # visited = []
    # while len(S) != 0:
    #     n = S.pop(0)
    #     if type(n) == TealConditionalBlock:
    #         if n.falseBlock is not None:
    #             S.insert(0, n.falseBlock)
    #         if n.trueBlock is not None:
    #             S.insert(0, n.trueBlock)
    #     else:
    #         for i, m in enumerate(n.getOutgoing()):
    #             if m in visited or m in S:
    #                 continue
    #             if type(m) != TealConditionalBlock and len(m.incoming) != 0:
    #                 S.append(m)
    #             else:
    #                 S.insert(0, m)
    #
    #     order.append(n)
    #     visited.append(n)
    #
    # return order
