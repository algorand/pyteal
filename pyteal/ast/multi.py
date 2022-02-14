from typing import Callable, List, Union, TYPE_CHECKING

from ..types import TealType
from ..ir import TealOp, Op, TealBlock
from .expr import Expr
from .leafexpr import LeafExpr
from .scratch import ScratchSlot

if TYPE_CHECKING:
    from ..compiler import CompileOptions


class MultiValue(LeafExpr):
    """Represents an operation that returns more than one value"""

    def __init__(
        self,
        op: Op,
        types: List[TealType],
        *,
        immediate_args: List[Union[int, str]] = None,
        args: List[Expr] = None
    ):
        """Create a new MultiValue.

        Args:
            op: The operation that returns values.
            types: The types of the returned values.
            immediate_args (optional): Immediate arguments for the op. Defaults to None.
            args (optional): Stack arguments for the op. Defaults to None.
        """
        super().__init__()
        self.op = op
        self.types = types
        self.immediate_args = immediate_args if immediate_args is not None else []
        self.args = args if args is not None else []

        self.output_slots = [ScratchSlot() for _ in self.types]
        self.reducer_set = False

    def outputReducer(self, reducer: Callable[..., Expr]) -> Expr:
        self.reducer = reducer
        self.reducer_set = True
        return self

    def __str__(self):
        ret_str = "(({}".format(self.op)
        for a in self.immediate_args:
            ret_str += " " + a.__str__()

        for a in self.args:
            ret_str += " " + a.__str__()
        ret_str += ") "

        ret_str += " ".join([slot.store().__str__() for slot in self.output_slots])
        ret_str += ")"

        return ret_str

    def __teal__(self, options: "CompileOptions"):
        tealOp = TealOp(self, self.op, *self.immediate_args)
        callStart, callEnd = TealBlock.FromOp(options, tealOp, *self.args)

        curEnd = callEnd
        for slot in self.output_slots:
            store = slot.store()
            storeStart, storeEnd = store.__teal__(options)
            curEnd.setNextBlock(storeStart)
            curEnd = storeEnd

        if self.reducer_set:
            input = [
                slot.load(self.types[i]) for i, slot in enumerate(self.output_slots)
            ]
            reducerStart, reducerEnd = self.reducer(*input).__teal__(options)
            curEnd.setNextBlock(reducerStart)
            return callStart, reducerEnd

        return callStart, curEnd

    def type_of(self):
        return TealType.none


MultiValue.__module__ = "pyteal"
