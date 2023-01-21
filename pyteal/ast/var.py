from typing import TYPE_CHECKING
from enum import Enum
from pyteal.ast.expr import Expr
from pyteal.ast.bytes import Bytes
from pyteal.ast.int import Int
from pyteal.ast.binaryexpr import BytesMul
from pyteal.ast.unaryexpr import Itob, Btoi
from pyteal.ast.seq import Seq
from pyteal.ast.naryexpr import Concat
from pyteal.ast.scratch import ScratchSlot
from pyteal.types import TealType, TealTypeError
from pyteal.ast import abi


if TYPE_CHECKING:
    from pyteal.compiler import CompileOptions


class Var(Expr):
    def __init__(
        self, val: Expr | int | bytes | str, type_cast: TealType = TealType.anytype
    ):
        match val:
            case str() | bytes():
                match type_cast:
                    case TealType.uint64:
                        val = Itob(Bytes(val))
                    case TealType.bytes | TealType.anytype:
                        val = Bytes(val)
                    case _:
                        raise Exception("wat")
            case int():
                match type_cast:
                    case TealType.uint64 | TealType.anytype:
                        val = Int(val)
                    case TealType.bytes:
                        val = Itob(Int(val))
                    case _:
                        raise Exception("wat")
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

        self.val = val
        self.slot = ScratchSlot()
        self.type = val.type_of()
        self.has_stored = False
        self.has_assigned = False

    def __str__(self):
        if self.has_stored:
            return self.slot.load(self.type).__str__()
        else:
            return self.slot.store(self.val).__str__()

    def __teal__(self, options: "CompileOptions"):
        if not self.has_stored:
            return self.store(self.val).__teal__(options)
        return self.load().__teal__(options)

    def load(self):
        return self.slot.load(self.type)

    def store(self, val: Expr):
        self.val = val
        self.has_stored = True
        return self.slot.store(val)

    def has_return(self):
        return False

    def type_of(self):
        # On assignment, nothing goes on the stack
        if not self.has_assigned:
            self.has_assigned = True
            return TealType.none
        else:
            return self.val.type_of()

    def __add__(self, other: "Var | Expr") -> Expr:
        match other:
            case Var():
                # treat assertion special because this is evaluated prior to assignment
                # so typecheck needs to be against val
                assert other.val.type_of() == self.val.type_of()
                match self.type:
                    case TealType.uint64:
                        return Seq(self.load() + other.load())
                    case TealType.bytes:
                        return Concat(self.load(), other.load())
                    case _:
                        raise Exception("????")
            case Expr():
                assert other.type_of() == self.val.type_of()
                match self.type:
                    case TealType.uint64:
                        return self.load() + other
                    case TealType.bytes:
                        return Concat(self.load(), other)
                    case _:
                        raise Exception("????")


Var.__module__ = "pyteal"
