from typing import List, cast

from ..ir import TealBlock, TealSimpleBlock, TealConditionalBlock

def sortBlocks(start: TealBlock) -> List[TealBlock]:
    """Topologically sort the graph which starts with the input TealBlock.

    Args:
        start: The starting point of the graph to sort.

    Returns:
        An ordered list of TealBlocks that is sorted such that every block is guaranteed to appear
        in the list before all of its outgoing blocks.
    """
    # bfs
    S = [start]
    order = []
    visited = []
    q = S
    while len(q) != 0:
        size = len(q)
        for i in range(size):
            n = q.pop(0)
            visited.append(n)
            order.append(n)
            for j, m in enumerate(n.getOutgoing()):
                if m not in visited:
                    visited.append(m)
                    q.append(m)

    return order
