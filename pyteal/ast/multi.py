from typing import Callable, List, Union, TYPE_CHECKING, cast

from pyteal.types import TealType
from pyteal.ir import TealOp, Op, TealBlock
from pyteal.ast.expr import Expr
from pyteal.ast.leafexpr import LeafExpr
from pyteal.ast.scratch import ScratchSlot
from pyteal.ast.seq import Seq
from pyteal.ast.scratch import ScratchStackStore

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class MultiValue(LeafExpr):
    """Represents an operation that returns more than one value"""

    def __init__(
        self,
        op: Op,
        types: List[TealType],
        *,
        immediate_args: List[Union[int, str]] | None = None,
        args: List[Expr] | None = None,
        compile_check: Callable[["CompileOptions"], None] = lambda _: None,
        root_expr: Expr | None = None,
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
        self.compile_check = compile_check

        self.output_slots = [ScratchSlot() for _ in self.types]
        self._sframes_container = root_expr

    def outputReducer(self, reducer: Callable[..., Expr]) -> Expr:
        input = [slot.load(self.types[i]) for i, slot in enumerate(self.output_slots)]
        return Seq(self, reducer(*input))

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
        self.compile_check(options)

        tealOp = TealOp(self, self.op, *self.immediate_args)
        callStart, callEnd = TealBlock.FromOp(options, tealOp, *self.args)

        curEnd = callEnd
        # the list is reversed in order to preserve the ordering of the opcode's returned
        # values. ie the output to stack [A, B, C] should correspond to C->output_slots[2]
        # B->output_slots[1], and A->output_slots[0].
        for slot in reversed(self.output_slots):
            store = cast(ScratchStackStore, slot.store())
            store._sframes_container = self._sframes_container
            storeStart, storeEnd = store.__teal__(options)
            curEnd.setNextBlock(storeStart)
            curEnd = storeEnd

        return callStart, curEnd

    def type_of(self):
        return TealType.none


MultiValue.__module__ = "pyteal"
