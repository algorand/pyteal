from typing import Callable, List

from ...ir import TealBlock

LocalOptimization = Callable[[TealBlock], TealBlock]

def applyLocalOptimizationToList(blocks: List[TealBlock], optimization: LocalOptimization) -> List[TealBlock]:
    return [optimization(block) for block in blocks]
