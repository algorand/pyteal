from typing import Union

from pyteal import (
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
    TealType,
)

from .utils import suffix
from .abi_type import ABIType


# TODO make a single Uint class that accepts bit size?


class Uint512(ABIType):
    stack_type = TealType.bytes
    byte_len = Int(512 // 8)

    def __init__(self, value: Union[int, Int, Bytes]):
        if isinstance(value, int):
            value = Bytes(value.to_bytes(self.byte_len, "big"))
        if isinstance(value, Int):
            value = Itob(value)
        self.value = value

    @classmethod
    def decode(cls, value: Bytes) -> "Uint512":
        return Uint512(Extract(value, Int(0), min(cls.byte_len, Len(value))))

    def encode(self) -> Expr:
        return Extract(
            Concat(BytesZero(self.byte_len - Len(self.value)), self.value),
            Int(0),
            self.byte_len,
        )


class Uint256(ABIType):
    stack_type = TealType.bytes
    byte_len = Int(256 // 8)

    def __init__(self, value: Union[int, Int, Bytes]):
        if isinstance(value, int):
            value = Bytes(value.to_bytes(self.byte_len, "big"))
        if isinstance(value, Int):
            value = Itob(value)
        self.value = value

    @classmethod
    def decode(cls, value: Bytes) -> "Uint256":
        return Uint256(Extract(value, Int(0), min(cls.byte_len, Len(value))))

    def encode(self) -> Expr:
        return Extract(
            Concat(BytesZero(self.byte_len - Len(self.value)), self.value),
            Int(0),
            self.byte_len,
        )


class Uint128(ABIType):
    stack_type = TealType.bytes
    byte_len = Int(128 // 8)

    def __init__(self, value: Union[int, Int, Bytes]):
        if isinstance(value, int):
            value = Bytes(value.to_bytes(self.byte_len, "big"))
        if isinstance(value, Int):
            value = Itob(value)

        self.value = value

    @classmethod
    def decode(cls, value: Bytes):
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

    def __init__(self, value: Union[int, Int]):
        if isinstance(value, int):
            value = Int(value)
        self.value = value

    @classmethod
    def decode(cls, value: Bytes) -> "Uint64":
        return Uint64(ExtractUint64(value, Int(0)))

    def encode(self) -> Expr:
        return Itob(self.value)


class Uint32(ABIType):
    stack_type = TealType.uint64
    byte_len = Int(32 // 8)

    def __init__(self, value: Union[int, Int]):
        if isinstance(value, int):
            value = Int(value)
        self.value = value

    @classmethod
    def decode(cls, value: Bytes):
        return Uint32(ExtractUint32(value, Int(0)))

    def encode(self) -> Expr:
        return suffix(Itob(self.value), self.byte_len)


class Uint16(ABIType):
    stack_type = TealType.uint64
    byte_len = Int(16 // 8)

    def __init__(self, value: Union[int, Int]):
        if isinstance(value, int):
            value = Int(value)
        self.value = value

    @classmethod
    def decode(cls, value: Bytes) -> "Uint16":
        return Uint16(If(Len(value) >= Int(2), ExtractUint16(value, Int(0)), Int(0)))

    def encode(self) -> Expr:
        return suffix(Itob(self.value), self.byte_len)


class Uint8(ABIType):
    stack_type = TealType.uint64
    byte_len = Int(1)

    def __init__(self, value: Union[int, Int]):
        if isinstance(value, int):
            value = Int(value)
        self.value = value

    @classmethod
    def decode(cls, value: Bytes) -> "Uint8":
        return Uint8(If(Len(value) >= Int(1), GetByte(value, Int(0)), Int(0)))

    def encode(self) -> Expr:
        return suffix(Itob(self.value), self.byte_len)
