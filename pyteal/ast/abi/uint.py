from typing import Union, cast
from abc import abstractmethod

from ...types import TealType
from ...errors import TealInputError
from ..expr import Expr
from ..seq import Seq
from ..assert_ import Assert
from ..substring import Suffix
from ..int import Int
from ..bytes import Bytes
from ..unaryexpr import Itob, Btoi
from ..binaryexpr import GetByte, ExtractUint16, ExtractUint32, ExtractUint64
from ..ternaryexpr import SetByte
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

    def __str__(self) -> str:
        return "uint{}".format(self.bit_size)


class Uint8(Uint):
    def __init__(
        self,
    ) -> None:
        super().__init__(8)

    def new_instance(self) -> "Uint8":
        return Uint8()

    def set(self, value: Union[int, Expr, "Uint8", "Byte"]) -> Expr:
        checked = False
        if type(value) is int:
            if value >= 2 ** self.bit_size:
                raise TealInputError(
                    "Value exceeds {} maximum: {}".format(
                        self.__class__.__name__, value
                    )
                )
            value = Int(value)
            checked = True

        if type(value) is Uint8 or type(value) is Byte:
            value = value.get()
            checked = True

        if checked:
            return self.stored_value.store(cast(Expr, value))

        return Seq(
            self.stored_value.store(cast(Expr, value)),
            Assert(self.stored_value.load() < Int(2 ** self.bit_size)),
        )

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        if startIndex is None:
            startIndex = Int(0)
        return self.stored_value.store(GetByte(encoded, startIndex))

    def encode(self) -> Expr:
        return SetByte(Bytes(b"\x00"), Int(0), self.get())


Uint8.__module__ = "pyteal"


class Byte(Uint8):
    def __init__(self) -> None:
        super().__init__()

    def new_instance(self) -> "Byte":
        return Byte()

    def __str__(self) -> str:
        return "byte"


Byte.__module__ = "pyteal"


class Uint16(Uint):
    def __init__(
        self,
    ) -> None:
        super().__init__(16)

    def new_instance(self) -> "Uint16":
        return Uint16()

    def set(self, value: Union[int, Expr, "Uint16"]) -> Expr:
        checked = False
        if type(value) is int:
            if value >= 2 ** self.bit_size:
                raise TealInputError("Value exceeds Uint16 maximum: {}".format(value))
            value = Int(value)
            checked = True

        if type(value) is Uint16:
            value = value.get()
            checked = True

        if checked:
            return self.stored_value.store(cast(Expr, value))

        return Seq(
            self.stored_value.store(cast(Expr, value)),
            Assert(self.stored_value.load() < Int(2 ** self.bit_size)),
        )

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        if startIndex is None:
            startIndex = Int(0)
        return self.stored_value.store(ExtractUint16(encoded, startIndex))

    def encode(self) -> Expr:
        return Suffix(Itob(self.get()), Int(6))


Uint16.__module__ = "pyteal"


class Uint32(Uint):
    def __init__(
        self,
    ) -> None:
        super().__init__(32)

    def new_instance(self) -> "Uint32":
        return Uint32()

    def set(self, value: Union[int, Expr, "Uint32"]) -> Expr:
        checked = False
        if type(value) is int:
            if value >= 2 ** self.bit_size:
                raise TealInputError("Value exceeds Uint32 maximum: {}".format(value))
            value = Int(value)
            checked = True

        if type(value) is Uint32:
            value = value.get()
            checked = True

        if checked:
            return self.stored_value.store(cast(Expr, value))

        return Seq(
            self.stored_value.store(cast(Expr, value)),
            Assert(self.stored_value.load() < Int(2 ** self.bit_size)),
        )

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        if startIndex is None:
            startIndex = Int(0)
        return self.stored_value.store(ExtractUint32(encoded, startIndex))

    def encode(self) -> Expr:
        return Suffix(Itob(self.get()), Int(4))


Uint32.__module__ = "pyteal"


class Uint64(Uint):
    def __init__(self) -> None:
        super().__init__(64)

    def new_instance(self) -> "Uint64":
        return Uint64()

    def set(self, value: Union[int, Expr, "Uint64"]) -> Expr:
        if type(value) is int:
            value = Int(value)
        if type(value) is Uint64:
            value = value.get()
        return self.stored_value.store(cast(Expr, value))

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        if startIndex is None:
            if endIndex is None and length is None:
                return self.stored_value.store(Btoi(encoded))
            startIndex = Int(0)
        return self.stored_value.store(ExtractUint64(encoded, startIndex))

    def encode(self) -> Expr:
        return Itob(self.get())


Uint64.__module__ = "pyteal"
