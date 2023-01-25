from typing import Final

from pyteal.ast import SubroutineDefinition
from pyteal.compiler.optimizer import OptimizeOptions
from pyteal.errors import TealInternalError
from pyteal.ir import Mode, TealSimpleBlock

MAX_PROGRAM_VERSION = 8
FRAME_POINTERS_VERSION = 8
DEFAULT_SCRATCH_SLOT_OPTIMIZE_VERSION = 9
MIN_PROGRAM_VERSION = 2
DEFAULT_PROGRAM_VERSION = MIN_PROGRAM_VERSION


"""Deprecated. Use MAX_PROGRAM_VERSION instead."""
MAX_TEAL_VERSION = MAX_PROGRAM_VERSION
"""Deprecated. Use MIN_PROGRAM_VERSION instead."""
MIN_TEAL_VERSION = MIN_PROGRAM_VERSION
"""Deprecated. Use DEFAULT_PROGRAM_VERSION instead."""
DEFAULT_TEAL_VERSION = DEFAULT_PROGRAM_VERSION


class CompileOptions:
    def __init__(
        self,
        *,
        mode: Mode = Mode.Signature,
        version: int = DEFAULT_PROGRAM_VERSION,
        optimize: OptimizeOptions | None = None,
    ) -> None:
        self.mode: Final[Mode] = mode
        self.version: Final[int] = version
        self.optimize: Final[OptimizeOptions] = optimize or OptimizeOptions()
        self.use_frame_pointers: Final[bool] = self.optimize.use_frame_pointers(
            self.version
        )

        self.currentSubroutine: SubroutineDefinition | None = None

        self.breakBlocksStack: list[list[TealSimpleBlock]] = []
        self.continueBlocksStack: list[list[TealSimpleBlock]] = []

    def setSubroutine(self, subroutine: SubroutineDefinition | None) -> None:
        self.currentSubroutine = subroutine

    def enterLoop(self) -> None:
        self.breakBlocksStack.append([])
        self.continueBlocksStack.append([])

    def isInLoop(self) -> bool:
        return len(self.breakBlocksStack) != 0

    def addLoopBreakBlock(self, block: TealSimpleBlock) -> None:
        if len(self.breakBlocksStack) == 0:
            raise TealInternalError("Cannot add break block when no loop is active")
        self.breakBlocksStack[-1].append(block)

    def addLoopContinueBlock(self, block: TealSimpleBlock) -> None:
        if len(self.continueBlocksStack) == 0:
            raise TealInternalError("Cannot add continue block when no loop is active")
        self.continueBlocksStack[-1].append(block)

    def exitLoop(self) -> tuple[list[TealSimpleBlock], list[TealSimpleBlock]]:
        if len(self.breakBlocksStack) == 0 or len(self.continueBlocksStack) == 0:
            raise TealInternalError("Cannot exit loop when no loop is active")
        return self.breakBlocksStack.pop(), self.continueBlocksStack.pop()
