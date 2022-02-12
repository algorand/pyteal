from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
from contextlib import AbstractContextManager

if TYPE_CHECKING:
    from ..ast import Expr, ScratchSlot, SubroutineDefinition


class TealComponent(ABC):
    def __init__(self, expr: Optional["Expr"]):
        self.expr = expr

    def getSlots(self) -> List["ScratchSlot"]:
        return []

    def assignSlot(self, slot: "ScratchSlot", location: int) -> None:
        pass

    def getSubroutines(self) -> List["SubroutineDefinition"]:
        return []

    def resolveSubroutine(self, subroutine: "SubroutineDefinition", label: str) -> None:
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

    class Context:

        checkExprEquality = True

        class ExprEqualityContext(AbstractContextManager):
            def __enter__(self):
                TealComponent.Context.checkExprEquality = False
                return self

            def __exit__(self, *args):
                TealComponent.Context.checkExprEquality = True
                return None

        @classmethod
        def ignoreExprEquality(cls):
            return cls.ExprEqualityContext()

        checkScratchSlotEquality = True

        class ScratchSlotEqualityContext(AbstractContextManager):
            def __enter__(self):
                TealComponent.Context.checkScratchSlotEquality = False

            def __exit__(self, *args):
                TealComponent.Context.checkScratchSlotEquality = True
                return None

        @classmethod
        def ignoreScratchSlotEquality(cls):
            return cls.ScratchSlotEqualityContext()


TealComponent.__module__ = "pyteal"
