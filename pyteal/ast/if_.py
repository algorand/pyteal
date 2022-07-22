from typing import TYPE_CHECKING

from pyteal.errors import (
    TealCompileError,
    TealInputError,
)
from pyteal.types import TealType, require_type
from pyteal.ir import TealSimpleBlock, TealConditionalBlock
from pyteal.ast.expr import Expr
from pyteal.ast.seq import _use_seq_if_multiple

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class If(Expr):
    """Simple two-way conditional expression."""

    def __init__(
        self, cond: Expr, thenBranch: Expr = None, elseBranch: Expr = None
    ) -> None:
        """Create a new If expression.

        When this If expression is executed, the condition will be evaluated, and if it produces a
        true value, thenBranch will be executed and used as the return value for this expression.
        Otherwise, elseBranch will be executed and used as the return value, if it is provided.

        Args:
            cond: The condition to check. Must evaluate to uint64.
            thenBranch: Expression to evaluate if the condition is true.
            elseBranch (optional): Expression to evaluate if the condition is false. Must evaluate
                to the same type as thenBranch, if provided. Defaults to None.
        """
        super().__init__()
        require_type(cond, TealType.uint64)
        # Flag to denote and check whether the new If().Then() syntax is being used
        self.alternateSyntaxFlag = False

        if thenBranch:
            if elseBranch:
                require_type(thenBranch, elseBranch.type_of())
            else:
                # If there is only a thenBranch, then it should evaluate to none type
                require_type(thenBranch, TealType.none)
        else:
            self.alternateSyntaxFlag = True

        self.cond = cond
        self.thenBranch = thenBranch
        self.elseBranch = elseBranch

    def __teal__(self, options: "CompileOptions"):
        if self.thenBranch is None:
            raise TealCompileError("If expression must have a thenBranch", self)

        condStart, condEnd = self.cond.__teal__(options)
        thenStart, thenEnd = self.thenBranch.__teal__(options)
        end = TealSimpleBlock([])

        branchBlock = TealConditionalBlock([])
        branchBlock.setTrueBlock(thenStart)

        condEnd.setNextBlock(branchBlock)
        thenEnd.setNextBlock(end)

        if self.elseBranch is None:
            branchBlock.setFalseBlock(end)
        else:
            elseStart, elseEnd = self.elseBranch.__teal__(options)
            branchBlock.setFalseBlock(elseStart)
            elseEnd.setNextBlock(end)

        return condStart, end

    def __str__(self):
        if self.thenBranch is None:
            raise TealCompileError("If expression must have a thenBranch", self)
        if self.elseBranch is None:
            return "(If {} {})".format(self.cond, self.thenBranch)
        return "(If {} {} {})".format(self.cond, self.thenBranch, self.elseBranch)

    def type_of(self):
        if self.thenBranch is None:
            raise TealCompileError("If expression must have a thenBranch", self)

        if self.elseBranch is None:
            # if there is only a thenBranch, it must evaluate to TealType.none
            require_type(self.thenBranch, TealType.none)

        return self.thenBranch.type_of()

    def has_return(self):
        if self.thenBranch is None:
            raise TealCompileError("If expression must have a thenBranch", self)

        if self.elseBranch is None:
            # return false in this case because elseBranch does not exist, so it can't have a return
            # op
            return False
        # otherwise, this expression has a return op only if both branches result in a return op
        return self.thenBranch.has_return() and self.elseBranch.has_return()

    def Then(self, thenBranch: Expr, *then_branch_multi: Expr):
        if not self.alternateSyntaxFlag:
            raise TealInputError("Cannot mix two different If syntax styles")

        thenBranch = _use_seq_if_multiple(thenBranch, *then_branch_multi)

        if not self.elseBranch:
            self.thenBranch = thenBranch
        else:
            if not isinstance(self.elseBranch, If):
                raise TealInputError("Else-Then block is malformed")
            self.elseBranch.Then(thenBranch)
        return self

    def ElseIf(self, cond):
        if not self.alternateSyntaxFlag:
            raise TealInputError("Cannot mix two different If syntax styles")

        if not self.elseBranch:
            self.elseBranch = If(cond)
        else:
            if not isinstance(self.elseBranch, If):
                raise TealInputError("Else-ElseIf block is malformed")
            self.elseBranch.ElseIf(cond)
        return self

    def Else(self, elseBranch: Expr, *else_branch_multi: Expr):
        if not self.alternateSyntaxFlag:
            raise TealInputError("Cannot mix two different If syntax styles")

        if not self.thenBranch:
            raise TealInputError("Must set Then branch before Else branch")

        elseBranch = _use_seq_if_multiple(elseBranch, *else_branch_multi)

        if not self.elseBranch:
            require_type(elseBranch, self.thenBranch.type_of())
            self.elseBranch = elseBranch
        else:
            if not isinstance(self.elseBranch, If):
                raise TealInputError("Else-Else block is malformed")
            self.elseBranch.Else(elseBranch)
        return self


If.__module__ = "pyteal"
