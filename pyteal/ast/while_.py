from typing import TYPE_CHECKING, Optional
from pyteal.ast.seq import _use_seq_if_multiple

from pyteal.errors import TealCompileError
from pyteal.types import TealType, require_type
from pyteal.ir import TealSimpleBlock, TealConditionalBlock
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class While(Expr):
    """While expression."""

    def __init__(self, cond: Expr) -> None:
        """Create a new While expression.

        When this While expression is executed, the condition will be evaluated, and if it produces a
        true value, doBlock will be executed and return to the start of the expression execution.
        Otherwise, no branch will be executed.

        Args:
            cond: The condition to check. Must evaluate to uint64.

        Example:
            .. code-block:: python

                i = ScratchVar()
                i.store(Int(0))
                While(i.load() < pt.Int(2))
                    .Do(Pop(Int(1)), i.store(i.load() + Int(1)))
        """
        super().__init__()
        require_type(cond, TealType.uint64)

        self.cond = cond
        self.doBlock: Optional[Expr] = None

    def __teal__(self, options: "CompileOptions"):
        if self.doBlock is None:
            raise TealCompileError("While expression must have a doBlock", self)

        options.enterLoop()

        condStart, condEnd = self.cond.__teal__(options)
        doStart, doEnd = self.doBlock.__teal__(options)
        end = TealSimpleBlock([])

        doEnd.setNextBlock(condStart)
        doEnd._sframes_container = self

        branchBlock = TealConditionalBlock([], root_expr=self)
        branchBlock.setTrueBlock(doStart)
        branchBlock.setFalseBlock(end)

        condEnd.setNextBlock(branchBlock)

        breakBlocks, continueBlocks = options.exitLoop()

        for block in breakBlocks:
            block.setNextBlock(end)

        for block in continueBlocks:
            block.setNextBlock(condStart)

        return condStart, end

    def __str__(self):
        if self.doBlock is None:
            raise TealCompileError("While expression must have a doBlock", self)

        return "(While {} {})".format(self.cond, self.doBlock)

    def type_of(self):
        if self.doBlock is None:
            raise TealCompileError("While expression must have a doBlock", self)
        return TealType.none

    def has_return(self):
        return False

    def Do(self, doBlock: Expr, *do_block_multi: Expr):
        if self.doBlock is not None:
            raise TealCompileError("While expression already has a doBlock", self)

        doBlock = _use_seq_if_multiple(doBlock, *do_block_multi)

        require_type(doBlock, TealType.none)

        self.doBlock = doBlock
        return self


While.__module__ = "pyteal"
