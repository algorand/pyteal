from typing import Union, List, Optional, TYPE_CHECKING

from pyteal.ir.tealcomponent import TealComponent
from pyteal.ir.labelref import LabelReference
from pyteal.ir.ops import Op
from pyteal.errors import TealInternalError

if TYPE_CHECKING:
    from pyteal.ast import Expr, ScratchSlot, SubroutineDefinition


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
        from pyteal.ast import ScratchSlot

        return [arg for arg in self.args if isinstance(arg, ScratchSlot)]

    def assignSlot(self, slot: "ScratchSlot", location: int) -> None:
        for i, arg in enumerate(self.args):
            if slot == arg:
                self.args[i] = location

    def getSubroutines(self) -> List["SubroutineDefinition"]:
        from pyteal.ast import SubroutineDefinition

        return [arg for arg in self.args if isinstance(arg, SubroutineDefinition)]

    def resolveSubroutine(self, subroutine: "SubroutineDefinition", label: str) -> None:
        for i, arg in enumerate(self.args):
            if subroutine == arg:
                self.args[i] = label

    def assemble(self) -> str:
        from pyteal.ast import ScratchSlot, SubroutineDefinition

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

        return "TealOp({})".format(", ".join(args))

    def __hash__(self) -> int:
        return (self.op, *self.args).__hash__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TealOp):
            return False

        if TealComponent.Context.checkExprEquality and self.expr is not other.expr:
            return False

        if not TealComponent.Context.checkScratchSlotEquality:
            from pyteal import ScratchSlot

            if len(self.args) != len(other.args):
                return False
            for myArg, otherArg in zip(self.args, other.args):
                if type(myArg) is ScratchSlot and type(otherArg) is ScratchSlot:
                    continue
                if myArg != otherArg:
                    return False
        elif self.args != other.args:
            return False

        return self.op == other.op


TealOp.__module__ = "pyteal"
