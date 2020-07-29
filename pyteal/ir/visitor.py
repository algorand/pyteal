from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tealblock import TealBlock
    from .tealop import TealOp

class IRVisitor(ABC):

    def visitBlock(self, block: 'TealBlock'):
        pass

    def visitOp(self, op: 'TealOp'):
        pass
