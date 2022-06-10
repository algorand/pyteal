from typing import (
    TypeVar,
    Union,
    Optional,
    Final,
    cast,
)
from abc import abstractmethod

from pyteal.types import TealType
from pyteal.errors import TealInputError
from pyteal.ast.scratchvar import ScratchVar
from pyteal.ast.expr import Expr
from pyteal.ast.seq import Seq
from pyteal.ast.assert_ import Assert
from pyteal.ast.substring import Suffix
from pyteal.ast.int import Int
from pyteal.ast.bytes import Bytes
from pyteal.ast.unaryexpr import Itob, Btoi
from pyteal.ast.binaryexpr import GetByte, ExtractUint16, ExtractUint32, ExtractUint64
from pyteal.ast.ternaryexpr import SetByte
from pyteal.ast.abi.type import ComputedValue, TypeSpec, BaseType

NUM_BITS_IN_BYTE = 8

SUPPORTED_UINT_SIZES = (8, 16, 32, 64)


def uint_storage_type(size: int) -> TealType:
    if size <= 64:
        return TealType.uint64
    return TealType.bytes


def uint_set(size: int, uintVar: ScratchVar, value: Union[int, Expr, "Uint"]) -> Expr:
    if size > 64:
        raise NotImplementedError(
            "Uint operations have not yet been implemented for bit sizes larger than 64"
        )

    checked = False
    if type(value) is int:
        if value >= 2**size:
            raise TealInputError("Value exceeds uint{} maximum: {}".format(size, value))
        value = Int(value)
        checked = True

    if isinstance(value, Uint):
        value = value.get()
        checked = True

    if checked or size == 64:
        return uintVar.store(cast(Expr, value))

    return Seq(
        uintVar.store(cast(Expr, value)),
        Assert(uintVar.load() < Int(2**size)),
    )


def uint_decode(
    size: int,
    uintVar: ScratchVar,
    encoded: Expr,
    startIndex: Optional[Expr],
    endIndex: Optional[Expr],
    length: Optional[Expr],
) -> Expr:
    if size > 64:
        raise NotImplementedError(
            "Uint operations have not yet been implemented for bit sizes larger than 64"
        )

    if size == 64:
        if startIndex is None:
            if endIndex is None and length is None:
                return uintVar.store(Btoi(encoded))
            startIndex = Int(0)
        return uintVar.store(ExtractUint64(encoded, startIndex))

    if startIndex is None:
        startIndex = Int(0)

    if size == 8:
        return uintVar.store(GetByte(encoded, startIndex))
    if size == 16:
        return uintVar.store(ExtractUint16(encoded, startIndex))
    if size == 32:
        return uintVar.store(ExtractUint32(encoded, startIndex))

    raise ValueError("Unsupported uint size: {}".format(size))


def uint_encode(size: int, uintVar: ScratchVar) -> Expr:
    if size > 64:
        raise NotImplementedError(
            "Uint operations have not yet been implemented for bit sizes larger than 64"
        )

    if size == 8:
        return SetByte(Bytes(b"\x00"), Int(0), uintVar.load())
    if size == 16:
        return Suffix(Itob(uintVar.load()), Int(6))
    if size == 32:
        return Suffix(Itob(uintVar.load()), Int(4))
    if size == 64:
        return Itob(uintVar.load())

    raise ValueError("Unsupported uint size: {}".format(size))


N = TypeVar("N", bound=int)


class UintTypeSpec(TypeSpec):
    def __init__(self, bit_size: int) -> None:
        super().__init__()
        if bit_size not in SUPPORTED_UINT_SIZES:
            raise TypeError("Unsupported uint size: {}".format(bit_size))
        self.size: Final = bit_size

    @abstractmethod
    def new_instance(self) -> "Uint":
        pass

    @abstractmethod
    def annotation_type(self) -> "type[Uint]":
        pass

    def bit_size(self) -> int:
        """Get the bit size of this uint type"""
        return self.size

    def is_dynamic(self) -> bool:
        return False

    def byte_length_static(self) -> int:
        return self.bit_size() // NUM_BITS_IN_BYTE

    def storage_type(self) -> TealType:
        return uint_storage_type(self.bit_size())

    def __eq__(self, other: object) -> bool:
        # NOTE: by this implementation, ByteTypeSpec() != Uint8TypeSpec()
        return (
            type(self) is type(other)
            and self.bit_size() == cast(UintTypeSpec, other).bit_size()
        )

    def __str__(self) -> str:
        return "uint{}".format(self.bit_size())


UintTypeSpec.__module__ = "pyteal"


class ByteTypeSpec(UintTypeSpec):
    def __init__(self) -> None:
        super().__init__(8)

    def new_instance(self) -> "Byte":
        return Byte()

    def annotation_type(self) -> "type[Byte]":
        return Byte

    def __str__(self) -> str:
        return "byte"


ByteTypeSpec.__module__ = "pyteal"


class Uint8TypeSpec(UintTypeSpec):
    def __init__(self) -> None:
        super().__init__(8)

    def new_instance(self) -> "Uint8":
        return Uint8()

    def annotation_type(self) -> "type[Uint8]":
        return Uint8


Uint8TypeSpec.__module__ = "pyteal"


class Uint16TypeSpec(UintTypeSpec):
    def __init__(self) -> None:
        super().__init__(16)

    def new_instance(self) -> "Uint16":
        return Uint16()

    def annotation_type(self) -> "type[Uint16]":
        return Uint16


Uint16TypeSpec.__module__ = "pyteal"


class Uint32TypeSpec(UintTypeSpec):
    def __init__(self) -> None:
        super().__init__(32)

    def new_instance(self) -> "Uint32":
        return Uint32()

    def annotation_type(self) -> "type[Uint32]":
        return Uint32


Uint32TypeSpec.__module__ = "pyteal"


class Uint64TypeSpec(UintTypeSpec):
    def __init__(self) -> None:
        super().__init__(64)

    def new_instance(self) -> "Uint64":
        return Uint64()

    def annotation_type(self) -> "type[Uint64]":
        return Uint64


Uint32TypeSpec.__module__ = "pyteal"


T = TypeVar("T", bound="Uint")


class Uint(BaseType):
    @abstractmethod
    def __init__(self, spec: UintTypeSpec) -> None:
        super().__init__(spec)

    def type_spec(self) -> UintTypeSpec:
        return cast(UintTypeSpec, super().type_spec())

    def get(self) -> Expr:
        return self.stored_value.load()

    def set(self: T, value: Union[int, Expr, "Uint", ComputedValue[T]]) -> Expr:
        if isinstance(value, ComputedValue):
            return self._set_with_computed_type(value)

        if isinstance(value, BaseType) and not (
            isinstance(value.type_spec(), UintTypeSpec)
            and self.type_spec().bit_size()
            == cast(UintTypeSpec, value.type_spec()).bit_size()
        ):
            raise TealInputError(
                "Type {} is not assignable to type {}".format(
                    value.type_spec(), self.type_spec()
                )
            )
        return uint_set(self.type_spec().bit_size(), self.stored_value, value)

    def decode(
        self,
        encoded: Expr,
        *,
        start_index: Expr = None,
        end_index: Expr = None,
        length: Expr = None,
    ) -> Expr:
        return uint_decode(
            self.type_spec().bit_size(),
            self.stored_value,
            encoded,
            start_index,
            end_index,
            length,
        )

    def encode(self) -> Expr:
        return uint_encode(self.type_spec().bit_size(), self.stored_value)


Uint.__module__ = "pyteal"


class Byte(Uint):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec())


Byte.__module__ = "pyteal"


class Uint8(Uint):
    def __init__(self) -> None:
        super().__init__(Uint8TypeSpec())


Uint8.__module__ = "pyteal"


class Uint16(Uint):
    def __init__(self) -> None:
        super().__init__(Uint16TypeSpec())


Uint16.__module__ = "pyteal"


class Uint32(Uint):
    def __init__(self) -> None:
        super().__init__(Uint32TypeSpec())


Uint32.__module__ = "pyteal"


class Uint64(Uint):
    def __init__(self) -> None:
        super().__init__(Uint64TypeSpec())


Uint64.__module__ = "pyteal"
