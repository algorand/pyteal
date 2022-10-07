from abc import ABC, abstractmethod
import ast
import executing
import inspect
from typing import cast, List, Optional, TYPE_CHECKING
from contextlib import AbstractContextManager

if TYPE_CHECKING:
    from pyteal.ast import Expr, ScratchSlot, SubroutineDefinition


class TealComponent(ABC):
    def __init__(self, expr: Optional["Expr"]):
        self.expr = expr

        # TODO: need to refactor/extract frame stuff
        self._frames: List[inspect.FrameInfo] | None
        # TODO: this is some sort of AST node, not Any:
        self._frame_nodes: List[ast.AST | None] | None

        if not self.expr:  # expr already has the frame info
            fs = inspect.stack()
            self._frames = fs
            self._frame_nodes = [
                cast(ast.AST | None, executing.Source.executing(f.frame).node)
                for f in fs
            ]

    def getSlots(self) -> List["ScratchSlot"]:
        return []

    def assignSlot(self, slot: "ScratchSlot", location: int) -> None:
        pass

    def getSubroutines(self) -> List["SubroutineDefinition"]:
        return []

    def resolveSubroutine(self, subroutine: "SubroutineDefinition", label: str) -> None:
        pass

    # TODO: unify/refactor + handle case when no tracing occurred
    def frames(self) -> List[inspect.FrameInfo] | None:
        return self.expr.frames if self.expr else self._frames

    # TODO: unify/refactor + handle case when no tracing occurred
    def frame_nodes(self) -> List[ast.AST | None] | None:
        return self.expr.frame_nodes if self.expr else self._frame_nodes

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
