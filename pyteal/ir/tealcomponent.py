from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..ast import ScratchSlot

class TealComponent(ABC):

    def getSlots(self) -> List['ScratchSlot']:
        return []
    
    def assignSlot(self, slot: 'ScratchSlot', location: int):
        pass
    
    @abstractmethod
    def assemble(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        pass

TealComponent.__module__ = "pyteal"
