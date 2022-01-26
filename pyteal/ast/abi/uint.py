from typing import Union, cast
from abc import abstractmethod

from ...types import TealType, require_type
from ..expr import Expr
from ..seq import Seq
from ..assert_ import Assert
from ..substring import Suffix
from ..int import Int
from ..unaryexpr import Itob, Not
from ..binaryexpr import ExtractUint64, ExtractUint16
from ..scratchvar import ScratchVar
from .type import ABIType, ABIValue

# TODO make a single Uint class that accepts bit size?

NUM_BITS_IN_BYTE = 8


class Uint(ABIValue):
    @abstractmethod
    def value(self) -> Expr:
        pass

    def byte_length(self) -> Expr:
        return Int(self.type.byte_length_static())


class Uint16Type(ABIType):
    def is_dynamic(self) -> bool:
        return False

    def byte_length_static(self) -> int:
        return 16 // NUM_BITS_IN_BYTE

    def decode(self, encoded: Expr, offset: Expr = None) -> "Uint16":
        if offset is None:
            offset = Int(0)
        return Uint16(ExtractUint16(encoded, offset))


Uint16Type.__module__ = "pyteal"


class Uint16(Uint):
    def __init__(self, value: Union[int, Expr]) -> None:
        super().__init__(Uint16Type())
        self.checked = False  # TODO: turn into bounds instead?
        if type(value) is int:
            if value >= 2 ** 16:
                raise ValueError("Value exceeds uint16 capacity")
            self.checked = True
            value = Int(value)
        value = cast(Expr, value)
        require_type(value, TealType.uint64)
        self.val = value

    def value(self) -> Expr:
        return self.val

    def encode(self) -> Expr:
        if self.checked:
            # value is known to fit in a uint16
            return Suffix(Itob(self.val), Int(6))
        # value might exceed a uint16, need to check at runtime
        v = ScratchVar(TealType.uint64)

        return Seq(
            v.store(self.val),
            Assert(Not(v.load() >> Int(2))),
            Suffix(Itob(v.load()), Int(6)),
        )

    def __add__(self, other: "Uint16") -> "Uint16":
        # TODO: check bounds
        return Uint16(self.value() + other.value())


Uint16.__module__ = "pyteal"


class Uint64Type(ABIType):
    def is_dynamic(self) -> bool:
        return False

    def byte_length_static(self) -> int:
        return 64 // NUM_BITS_IN_BYTE

    def decode(self, encoded: Expr, offset: Expr = None) -> "Uint64":
        if offset is None:
            offset = Int(0)
        return Uint64(ExtractUint64(encoded, offset))


Uint64Type.__module__ = "pyteal"


class Uint64(Uint):
    def __init__(self, value: Union[int, Expr]) -> None:
        super().__init__(Uint64Type())
        if type(value) is int:
            value = Int(value)
        value = cast(Expr, value)
        require_type(value, TealType.uint64)
        self.val = value

    def value(self) -> Expr:
        return self.val

    def encode(self) -> Expr:
        return Itob(self.val)

    def __add__(self, other: "Uint64") -> "Uint64":
        return Uint64(self.value() + other.value())

    # TODO: other operator overloads


Uint64.__module__ = "pyteal"
