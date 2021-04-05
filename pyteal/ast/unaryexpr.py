from typing import TYPE_CHECKING

from ..types import TealType, require_type
from ..ir import TealOp, Op, TealBlock
from .expr import Expr

if TYPE_CHECKING:
    from ..compiler import CompileOptions

class UnaryExpr(Expr):
    """An expression with a single argument."""

    def __init__(self, op: Op, inputType: TealType, outputType: TealType, arg: Expr) -> None:
        super().__init__()
        require_type(arg.type_of(), inputType)
        self.op = op
        self.outputType = outputType
        self.arg = arg

    def __teal__(self, options: 'CompileOptions'):
        return TealBlock.FromOp(options, TealOp(self, self.op), self.arg)

    def __str__(self):
        return "({} {})".format(self.op, self.arg)

    def type_of(self):
        return self.outputType

UnaryExpr.__module__ = "pyteal"

def Btoi(arg: Expr) -> UnaryExpr:
    """Convert a byte string to a uint64."""
    return UnaryExpr(Op.btoi, TealType.bytes, TealType.uint64, arg)

def Itob(arg: Expr) -> UnaryExpr:
    """Convert a uint64 string to a byte string."""
    return UnaryExpr(Op.itob, TealType.uint64, TealType.bytes, arg)

def Len(arg: Expr) -> UnaryExpr:
    """Get the length of a byte string."""
    return UnaryExpr(Op.len, TealType.bytes, TealType.uint64, arg)

def Sha256(arg: Expr) -> UnaryExpr:
    """Get the SHA-256 hash of a byte string."""
    return UnaryExpr(Op.sha256, TealType.bytes, TealType.bytes, arg)

def Sha512_256(arg: Expr) -> UnaryExpr:
    """Get the SHA-512/256 hash of a byte string."""
    return UnaryExpr(Op.sha512_256, TealType.bytes, TealType.bytes, arg)

def Keccak256(arg: Expr) -> UnaryExpr:
    """Get the KECCAK-256 hash of a byte string."""
    return UnaryExpr(Op.keccak256, TealType.bytes, TealType.bytes, arg)

def Not(arg: Expr) -> UnaryExpr:
    """Get the logical inverse of a uint64.

    If the argument is 0, then this will produce 1. Otherwise this will produce 0.
    """
    return UnaryExpr(Op.logic_not, TealType.uint64, TealType.uint64, arg)

def BitwiseNot(arg: Expr) -> UnaryExpr:
    """Get the bitwise inverse of a uint64.
    
    Produces ~arg.
    """
    return UnaryExpr(Op.bitwise_not, TealType.uint64, TealType.uint64, arg)

def Pop(arg: Expr) -> UnaryExpr:
    """Pop a value from the stack."""
    return UnaryExpr(Op.pop, TealType.anytype, TealType.none, arg)

def Return(arg: Expr) -> UnaryExpr:
    """Immediately exit the program with the given success value."""
    return UnaryExpr(Op.return_, TealType.uint64, TealType.none, arg)

def Balance(account: Expr) -> UnaryExpr:
    """Get the balance of a user in microAlgos.

    Argument must be an index into Txn.Accounts that corresponds to the account to read from. It
    must evaluate to uint64.

    This operation is only permitted in application mode.
    """
    return UnaryExpr(Op.balance, TealType.uint64, TealType.uint64, account)

def MinBalance(account: Expr) -> UnaryExpr:
    """Get the minimum balance of a user in microAlgos.

    For more information about minimum balances, see: https://developer.algorand.org/docs/features/accounts/#minimum-balance

    Argument must be an index into Txn.Accounts that corresponds to the account to read from. It
    must evaluate to uint64.

    Requires TEAL version 3 or higher. This operation is only permitted in application mode.
    """
    return UnaryExpr(Op.min_balance, TealType.uint64, TealType.uint64, account)
