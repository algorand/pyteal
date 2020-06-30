from ..types import TealType, require_type
from .expr import Expr

class UnaryExpr(Expr):
    """An expression with a single argument."""

    def __init__(self, op: str, inputType: TealType, outputType: TealType, arg: Expr) -> None:
        require_type(arg.type_of(), inputType)
        self.op = op
        self.outputType = outputType
        self.arg = arg

    def __teal__(self):
        teal = self.arg.__teal__()
        teal.append([self.op])
        return teal

    def __str__(self):
        return "({} {})".format(self.op, self.arg)

    def type_of(self):
        return self.outputType

def Btoi(arg: Expr):
    """Convert a byte string to a uint64."""
    return UnaryExpr("btoi", TealType.bytes, TealType.uint64, arg)

def Itob(arg: Expr):
    """Convert a uint64 string to a byte string."""
    return UnaryExpr("itob", TealType.uint64, TealType.bytes, arg)

def Len(arg: Expr):
    """Get the length of a byte string."""
    return UnaryExpr("len", TealType.bytes, TealType.uint64, arg)

def Sha256(arg: Expr):
    """Get the SHA-256 hash of a byte string."""
    return UnaryExpr("sha256", TealType.bytes, TealType.bytes, arg)

def Sha512_256(arg: Expr):
    """Get the SHA-512/256 hash of a byte string."""
    return UnaryExpr("sha512_256", TealType.bytes, TealType.bytes, arg)

def Keccak256(arg: Expr):
    """Get the KECCAK-256 hash of a byte string."""
    return UnaryExpr("keccak256", TealType.bytes, TealType.bytes, arg)

def Pop(arg: Expr):
    """Pop a value from the stack."""
    return UnaryExpr("pop", TealType.anytype, TealType.none, arg)
