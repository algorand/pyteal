from typing import Union, cast

from . import (
    Bytes,
    BytesZero,
    Concat,
    Expr,
    Extract,
    ExtractUint16,
    ExtractUint32,
    ExtractUint64,
    GetByte,
    If,
    Int,
    Itob,
    Len,
)

from ..types import TealType

from .abi_utils import suffix
from .abi_type import ABIType


# TODO make a single Uint class that accepts bit size?


class Uint512(ABIType):
    stack_type = TealType.bytes
    _byte_len = 512 // 8
    byte_len = Int(_byte_len)

    def __init__(self, value: Union[int, Int, Bytes, Expr]):
        if isinstance(value, int):
            value = Bytes(value.to_bytes(self._byte_len, "big"))
        if isinstance(value, Int):
            value = Itob(cast(Int, value))
        value = cast(Expr, value)
        self.value = value

    @classmethod
    def decode(cls, value: Expr) -> "Uint512":
        return Uint512(Extract(value, Int(0), min(cls.byte_len, Len(value))))

    def encode(self) -> Expr:
        return Extract(
            Concat(BytesZero(self.byte_len - Len(self.value)), self.value),
            Int(0),
            self.byte_len,
        )


class Uint256(ABIType):
    stack_type = TealType.bytes
    _byte_len = 256 // 8
    byte_len = Int(_byte_len)

    def __init__(self, value: Union[int, Int, Bytes, Expr]):
        if isinstance(value, int):
            value = Bytes(value.to_bytes(self._byte_len, "big"))
        if isinstance(value, Int):
            value = Itob(value)
        value = cast(Expr, value)
        self.value = value

    @classmethod
    def decode(cls, value: Expr) -> "Uint256":
        return Uint256(Extract(value, Int(0), min(cls.byte_len, Len(value))))

    def encode(self) -> Expr:
        return Extract(
            Concat(BytesZero(self.byte_len - Len(self.value)), self.value),
            Int(0),
            self.byte_len,
        )


class Uint128(ABIType):
    stack_type = TealType.bytes
    _byte_len = 128 // 8
    byte_len = Int(_byte_len)

    def __init__(self, value: Union[int, Int, Bytes, Expr]):
        if isinstance(value, int):
            value = Bytes(value.to_bytes(self._byte_len, "big"))
        if isinstance(value, Int):
            value = Itob(value)
        value = cast(Expr, value)
        self.value = value

    @classmethod
    def decode(cls, value: Expr):
        return Uint128(Extract(value, Int(0), min(cls.byte_len, Len(value))))

    def encode(self) -> Expr:
        return Extract(
            Concat(BytesZero(self.byte_len - Len(self.value)), self.value),
            Int(0),
            self.byte_len,
        )


class Uint64(ABIType):
    stack_type = TealType.uint64
    byte_len = Int(64 // 8)

    def __init__(self, value: Union[int, Int, Expr]):
        if isinstance(value, int):
            value = Int(value)
        value = cast(Expr, value)
        self.value = value

    @classmethod
    def decode(cls, value: Expr) -> "Uint64":
        return Uint64(ExtractUint64(value, Int(0)))

    def encode(self) -> Expr:
        return Itob(self.value)


class Uint32(ABIType):
    stack_type = TealType.uint64
    byte_len = Int(32 // 8)

    def __init__(self, value: Union[int, Int, Expr]):
        if isinstance(value, int):
            value = Int(value)
        value = cast(Expr, value)
        self.value = value

    @classmethod
    def decode(cls, value: Expr):
        return Uint32(ExtractUint32(value, Int(0)))

    def encode(self) -> Expr:
        return suffix(Itob(self.value), self.byte_len)


class Uint16(ABIType):
    stack_type = TealType.uint64
    byte_len = Int(16 // 8)

    def __init__(self, value: Union[int, Int, Expr]):
        if isinstance(value, int):
            value = Int(value)
        value = cast(Expr, value)
        self.value = value

    @classmethod
    def decode(cls, value: Expr) -> "Uint16":
        return Uint16(If(Len(value) >= Int(2), ExtractUint16(value, Int(0)), Int(0)))

    def encode(self) -> Expr:
        return suffix(Itob(self.value), self.byte_len)


class Uint8(ABIType):
    stack_type = TealType.uint64
    byte_len = Int(1)

    def __init__(self, value: Union[int, Int, Expr]):
        if isinstance(value, int):
            value = Int(value)
        value = cast(Expr, value)
        self.value = value

    @classmethod
    def decode(cls, value: Expr) -> "Uint8":
        return Uint8(If(Len(value) >= Int(1), GetByte(value, Int(0)), Int(0)))

    def encode(self) -> Expr:
        return suffix(Itob(self.value), self.byte_len)


Uint512.__module__ = "pyteal"
Uint256.__module__ = "pyteal"
Uint128.__module__ = "pyteal"
Uint64.__module__ = "pyteal"
Uint32.__module__ = "pyteal"
Uint16.__module__ = "pyteal"
Uint8.__module__ = "pyteal"
