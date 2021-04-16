from typing import List

from ..ir import TealBlock

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

    while len(S) != 0:
        n = S.pop(0)
        order.append(n)
        for i, m in enumerate(n.getOutgoing()):
            for i, block in enumerate(m.incoming):
                if n is block:
                    m.incoming.pop(i)
                    break
            if len(m.incoming) == 0:
                if i == 0:
                    S.insert(0, m)
                else:
                    S.append(m)
    
    return order
