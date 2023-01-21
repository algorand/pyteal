from typing import TYPE_CHECKING
from pyteal.ast.expr import Expr
from pyteal.ast.bytes import Bytes
from pyteal.ast.int import Int
from pyteal.ast.unaryexpr import Itob, Btoi
from pyteal.ast.naryexpr import Concat
from pyteal.ast.scratch import ScratchSlot
from pyteal.types import TealType, TealTypeError


if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


def _type_cast(
    val: Expr | int | bytes | str, type_cast: TealType = TealType.anytype
) -> Expr:
    match val:
        case str() | bytes():
            match type_cast:
                case TealType.uint64:
                    val = Itob(Bytes(val))
                case TealType.bytes | TealType.anytype:
                    val = Bytes(val)
                case _:
                    raise Exception("bytes or str cant map to none")
        case int():
            match type_cast:
                case TealType.uint64 | TealType.anytype:
                    val = Int(val)
                case TealType.bytes:
                    val = Itob(Int(val))
                case _:
                    raise Exception("int cant map to none")
        case Expr():
            got = val.type_of()
            match got:
                case TealType.uint64:
                    match type_cast:
                        case TealType.bytes:
                            val = Btoi(val)
                        case TealType.uint64 | TealType.anytype:
                            pass
                        case _:
                            raise TealTypeError(type_cast, got)
                case TealType.bytes:
                    match type_cast:
                        case TealType.uint64:
                            val = Itob(val)
                        case TealType.bytes | TealType.anytype:
                            pass
                        case _:
                            raise TealTypeError(type_cast, got)
                case TealType.anytype:
                    pass
                case _:
                    raise TealTypeError(type_cast, got)
    return val


class Var(Expr):
    def __init__(
        self, val: Expr | int | bytes | str, type_cast: TealType = TealType.anytype
    ):
        self.val = _type_cast(val, type_cast)
        self.slot = ScratchSlot()
        self.type = self.val.type_of()

    def __str__(self):
        return self.slot.load(self.type).__str__()

    def __teal__(self, options: "CompileOptions"):
        return self.load().__teal__(options)

    def assign(self) -> Expr:
        return self.store(self.val)

    def load(self) -> Expr:
        return self.slot.load(self.type)

    def store(self, val: Expr) -> Expr:
        self.val = val
        self.type = val.type_of()
        return self.slot.store(val)

    def has_return(self):
        return False

    def type_of(self):
        return self.type

    def incr(self) -> Expr:
        assert self.type == TealType.uint64
        return self.store(self.load() + Int(1))

    def decr(self) -> Expr:
        assert self.type == TealType.uint64
        return self.store(self.load() - Int(1))

    def __add__(self, other: Expr) -> Expr:
        assert other.type_of() == self.type_of()
        match self.type:
            case TealType.uint64:
                return self.load() + other
            case TealType.bytes:
                return Concat(self.load(), other)
            case _:
                raise Exception("howd we get here")


Var.__module__ = "pyteal"
