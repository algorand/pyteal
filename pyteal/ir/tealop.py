from typing import cast, Union, List, Optional, TYPE_CHECKING

from .tealcomponent import TealComponent
from .labelref import LabelReference
from .ops import Op
from ..errors import TealInternalError

if TYPE_CHECKING:
    from ..ast import Expr, ScratchSlot, SubroutineDefinition


class TealOp(TealComponent):
    def __init__(
        self,
        expr: Optional["Expr"],
        op: Op,
        *args: Union[int, str, LabelReference, "ScratchSlot", "SubroutineDefinition"]
    ) -> None:
        super().__init__(expr)
        self.op = op
        self.args = list(args)

    def getOp(self) -> Op:
        return self.op

    def getSlots(self) -> List["ScratchSlot"]:
        from ..ast import ScratchSlot

        return [arg for arg in self.args if isinstance(arg, ScratchSlot)]

    def assignSlot(self, slot: "ScratchSlot", location: int) -> None:
        for i, arg in enumerate(self.args):
            if slot == arg:
                self.args[i] = location

    def getSubroutines(self) -> List["SubroutineDefinition"]:
        from ..ast import SubroutineDefinition

        return [arg for arg in self.args if isinstance(arg, SubroutineDefinition)]

    def resolveSubroutine(self, subroutine: "SubroutineDefinition", label: str) -> None:
        for i, arg in enumerate(self.args):
            if subroutine == arg:
                self.args[i] = label

    def assemble(self) -> str:
        from ..ast import ScratchSlot, SubroutineDefinition

        parts = [str(self.op)]
        for arg in self.args:
            if isinstance(arg, ScratchSlot):
                raise TealInternalError("Slot not assigned: {}".format(arg))

            if isinstance(arg, SubroutineDefinition):
                raise TealInternalError("Subroutine not resolved: {}".format(arg))

            if isinstance(arg, int):
                parts.append(str(arg))
            elif isinstance(arg, LabelReference):
                parts.append(arg.getLabel())
            else:
                parts.append(arg)

        return " ".join(parts)

    def __repr__(self) -> str:
        args = [str(self.op)]
        for a in self.args:
            args.append(repr(a))

        return "TealOp({}, {})".format(self.expr, ", ".join(args))

    def __hash__(self) -> int:
        return (self.op, *self.args).__hash__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealOp):
            return False
        if TealComponent.Context.checkExpr and self.expr is not other.expr:
            return False
        return self.op == other.op and self.args == other.args


TealOp.__module__ = "pyteal"
