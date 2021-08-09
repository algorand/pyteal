from typing import List

from ..ir import TealBlock, TealSimpleBlock

def sortBlocks(start: TealBlock) -> List[TealBlock]:
    """Topologically sort the graph which starts with the input TealBlock.

    Args:
        start: The starting point of the graph to sort.

    Returns:
        An ordered list of TealBlocks that is sorted such that every block is guaranteed to appear
        in the list before all of its outgoing blocks.
    """
    # based on Kahn's algorithm from https://en.wikipedia.org/wiki/Topological_sorting
    S = [start]
    order = []
    visited = []
    visiting = []
    emptyBlock = TealSimpleBlock([])
    while len(S) != 0:
        n = S.pop()
        visiting.append(n)
        for i, m in enumerate(n.getOutgoing()):
            if m in visiting or m in visited or m == emptyBlock:
                continue
            S.append(m)
        visited.append(n)
        order.append(n)
    order.append(emptyBlock)
    return order
