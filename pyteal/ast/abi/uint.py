from typing import Union, cast
from abc import abstractmethod

from ...types import TealType
from ..expr import Expr
from ..seq import Seq
from ..assert_ import Assert
from ..substring import Suffix
from ..int import Int
from ..unaryexpr import Itob, Not
from ..binaryexpr import ExtractUint64, ExtractUint16
from .type import Type

NUM_BITS_IN_BYTE = 8


class Uint(Type):
    def __init__(self, bit_size: int) -> None:
        valueType = TealType.uint64 if bit_size <= 64 else TealType.bytes
        super().__init__(valueType)
        self.bit_size = bit_size

    def has_same_type_as(self, other: Type) -> bool:
        return isinstance(other, Uint) and self.bit_size == other.bit_size

    def is_dynamic(self) -> bool:
        return False

    def bits(self) -> int:
        return self.bit_size

    def byte_length_static(self) -> int:
        return self.bit_size // NUM_BITS_IN_BYTE

    def get(self) -> Expr:
        return self.stored_value.load()

    @abstractmethod
    def set(self, value: Union[int, Expr]) -> Expr:
        pass


class Uint16(Uint):
    def __init__(
        self,
    ) -> None:
        super().__init__(16)

    def new_instance(self) -> "Uint16":
        return Uint16()

    def set(self, value: Union[int, Expr]) -> Expr:
        if type(value) is int:
            if value >= 2 ** 16:
                raise ValueError("Value exceeds Uint16 maximum: {}".format(value))
            value = Int(value)
        # TODO: check dynamic value bounds?
        return self.stored_value.store(cast(Expr, value))

    def decode(self, encoded: Expr, offset: Expr, length: Expr) -> Expr:
        return Seq(
            Assert(length == Int(self.byte_length_static())),  # TODO: remove?
            self.set(ExtractUint16(encoded, offset)),
        )

    def encode(self) -> Expr:
        # value might exceed a uint16, need to check at runtime
        return Seq(
            Assert(Not(self.get() >> Int(16))),
            Suffix(Itob(self.get()), Int(6)),
        )


Uint16.__module__ = "pyteal"


class Uint64(Uint):
    def __init__(self) -> None:
        super().__init__(64)

    def new_instance(self) -> "Uint64":
        return Uint64()

    def set(self, value: Union[int, Expr]) -> Expr:
        if type(value) is int:
            value = Int(value)
        return self.stored_value.store(cast(Expr, value))

    def decode(self, encoded: Expr, offset: Expr, length: Expr) -> Expr:
        return Seq(
            Assert(length == Int(self.byte_length_static())),  # TODO: remove?
            self.set(ExtractUint64(encoded, offset)),
        )

    def encode(self) -> Expr:
        return Itob(self.get())


Uint64.__module__ = "pyteal"
