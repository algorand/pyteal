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
    S = [start]
    order = []
    visited = []
    while len(S) != 0:
        n = S.pop(0)
        if type(n)==TealConditionalBlock:
            S.insert(0, n.falseBlock)
            S.insert(0, n.trueBlock)
        else:
            for i, m in enumerate(n.getOutgoing()):
                if m in visited or m in S:
                    continue
                if type(m) != TealConditionalBlock and len(m.incoming) != 0:
                    S.append(m)
                else:
                    S.insert(0, m)

        order.append(n)
        visited.append(n)

    return order

