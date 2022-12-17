from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, List, Optional, cast

from pyteal.stack_frame import Frames

if TYPE_CHECKING:
    from pyteal.ast import Expr, ScratchSlot, SubroutineDefinition


class TealComponent(ABC):
    def __init__(self, expr: Optional["Expr"]):
        self.expr = expr

        self._frames: Optional[Frames] = None
        if not self.expr:  # expr already has the frame info
            self._frames = Frames()

    def getSlots(self) -> List["ScratchSlot"]:
        return []

    def assignSlot(self, slot: "ScratchSlot", location: int) -> None:
        pass

    def getSubroutines(self) -> List["SubroutineDefinition"]:
        return []

    def resolveSubroutine(self, subroutine: "SubroutineDefinition", label: str) -> None:
        pass

    def frames(self) -> Frames:
        if self.expr:
            root_expr = getattr(self.expr, "root_expr", None) or self.expr
            return root_expr.frames

        return cast(Frames, self._frames)

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
            """When comparing TealOps, do not verify the equality of any ScratchSlot arguments.

            This is commonly used in testing to verify the that two control flow graphs contains the
            same operations, but may use different ScratchSlots in them. In this case, you will most
            likely want to also use use the following code after comparing with this option enabled:

                .. code-block:: python

                    TealBlock.MatchScratchSlotReferences(
                        TealBlock.GetReferencedScratchSlots(actual),
                        TealBlock.GetReferencedScratchSlots(expected),
                    )

            This ensures that the ScratchSlot usages between the two control flow graphs is
            equivalent. See :any:`TealBlock.MatchScratchSlotReferences` for more info.
            """
            return cls.ScratchSlotEqualityContext()


TealComponent.__module__ = "pyteal"
