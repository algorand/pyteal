from typing import Sequence, cast, TYPE_CHECKING

from pyteal.types import TealType, require_type
from pyteal.errors import TealInputError
from pyteal.ir import TealOp, Op, TealSimpleBlock
from pyteal.ast.expr import Expr

if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class NaryExpr(Expr):
    """N-ary expression base class.

    This type of expression takes an arbitrary number of arguments.
    """

    def __init__(
        self, op: Op, inputType: TealType, outputType: TealType, args: Sequence[Expr]
    ):
        super().__init__()
        if len(args) == 0:
            raise TealInputError("NaryExpr requires at least one child")
        for arg in args:
            if not isinstance(arg, Expr):
                raise TealInputError(
                    "Argument is not a PyTeal expression: {}".format(arg)
                )
            require_type(arg, inputType)
        self.op = op
        self.outputType = outputType
        self.args = args

    def __teal__(self, options: "CompileOptions"):
        start = None
        end = None
        for i, arg in enumerate(self.args):
            argStart, argEnd = arg.__teal__(options)
            if i == 0:
                start = argStart
                end = argEnd
            else:
                cast(TealSimpleBlock, end).setNextBlock(argStart)
                opBlock = TealSimpleBlock([TealOp(self, self.op)])
                argEnd.setNextBlock(opBlock)
                end = opBlock

        return start, end

    def __str__(self):
        ret_str = "(" + str(self.op).title().replace("_", "")
        for a in self.args:
            ret_str += " " + a.__str__()
        ret_str += ")"
        return ret_str

    def type_of(self):
        return self.outputType

    def has_return(self):
        return False


NaryExpr.__module__ = "pyteal"


def Add(*args: Expr) -> Expr:
    """Numerical addition.

    Produces the sum of all the input arguments.

    All arguments must be PyTeal expressions that evaluate to uint64, and there must be at least one
    argument.

    Example:
        ``Add(Int(1), Int(2), Int(3))``
    """
    return NaryExpr(Op.add, TealType.uint64, TealType.uint64, args)


def Mul(*args: Expr) -> Expr:
    """Numerical multiplication.

    Produces the product of all the input arguments.

    All arguments must be PyTeal expressions that evaluate to uint64, and there must be at least one
    argument.

    Example:
        ``Mul(Int(2), Int(3), Int(4))``
    """
    return NaryExpr(Op.mul, TealType.uint64, TealType.uint64, args)


def And(*args: Expr) -> Expr:
    """Logical and expression.

    Produces 1 if all arguments are nonzero. Otherwise produces 0.

    All arguments must be PyTeal expressions that evaluate to uint64, and there must be at least one
    argument.

    Example:
        ``And(Txn.amount() == Int(500), Txn.fee() <= Int(10))``
    """
    return NaryExpr(Op.logic_and, TealType.uint64, TealType.uint64, args)


def Or(*args: Expr) -> Expr:
    """Logical or expression.

    Produces 1 if any argument is nonzero. Otherwise produces 0.

    All arguments must be PyTeal expressions that evaluate to uint64, and there must be at least one
    argument.
    """
    return NaryExpr(Op.logic_or, TealType.uint64, TealType.uint64, args)


def Concat(*args: Expr) -> Expr:
    """Concatenate byte strings.

    Produces a new byte string consisting of the contents of each of the passed in byte strings
    joined together.

    All arguments must be PyTeal expressions that evaluate to bytes, and there must be at least one
    argument.

    Example:
        ``Concat(Bytes("hello"), Bytes(" "), Bytes("world"))``
    """
    return NaryExpr(Op.concat, TealType.bytes, TealType.bytes, args)
