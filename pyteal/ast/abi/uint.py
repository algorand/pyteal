from typing import (
    Generic,
    TypeVar,
    Union,
    Optional,
    cast,
    Type as PyType,
    Literal,
    get_origin,
    get_args,
)
from abc import abstractmethod

from ...types import TealType
from ...errors import TealInputError
from ..scratchvar import ScratchVar
from ..expr import Expr
from ..seq import Seq
from ..assert_ import Assert
from ..substring import Suffix
from ..int import Int
from ..bytes import Bytes
from ..unaryexpr import Itob
from ..binaryexpr import GetByte, ExtractUint16, ExtractUint32, ExtractUint64
from ..ternaryexpr import SetByte
from .type import Type

NUM_BITS_IN_BYTE = 8

SUPPORTED_SIZES = (8, 16, 32, 64)


def uint_storage_type(size: int) -> TealType:
    if size <= 64:
        return TealType.uint64
    return TealType.bytes


def uint_set(size: int, uintVar: ScratchVar, value: Union[int, Expr, "Uint"]) -> Expr:
    checked = False
    if type(value) is int:
        if value >= 2 ** size:
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
        Assert(uintVar.load() < Int(2 ** size)),
    )


def uint_decode(
    size: int,
    uintVar: ScratchVar,
    encoded: Expr,
    startIndex: Optional[Expr],
    endIndex: Optional[Expr],
    length: Optional[Expr],
) -> Expr:
    if startIndex is None:
        startIndex = Int(0)

    if size == 8:
        return uintVar.store(GetByte(encoded, startIndex))
    if size == 16:
        return uintVar.store(ExtractUint16(encoded, startIndex))
    if size == 32:
        return uintVar.store(ExtractUint32(encoded, startIndex))
    if size == 64:
        return uintVar.store(ExtractUint64(encoded, startIndex))

    raise ValueError("Unsupported uint size: {}".format(size))


def uint_encode(size: int, uintVar: ScratchVar) -> Expr:
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


class Uint(Type, Generic[N]):
    def __class_getitem__(cls, size: int) -> PyType["Uint"]:
        if get_origin(size) is Literal:
            args = get_args(size)
            assert len(args) == 1
            assert type(args[0]) is int
            size = args[0]

        assert isinstance(size, int)

        if size not in SUPPORTED_SIZES:
            raise ValueError("Unsupported uint size: {}".format(size))

        class SizedUint(Uint):
            def __class_getitem__(cls, _):
                # prevent Uint[A][B]
                raise TypeError("Cannot index into Uint[{}]".format(size))

            @classmethod
            def bit_size(cls) -> int:
                return size

        return SizedUint

    @classmethod
    def has_same_type_as(cls, other: Union[PyType[Type], Type]) -> bool:
        return (
            isinstance(other, Uint) or issubclass(cast(PyType[Type], other), Uint)
        ) and cls.bit_size() == cast(Union[PyType[Uint], Uint], other).bit_size()

    @classmethod
    def is_dynamic(cls) -> bool:
        return False

    @classmethod
    def byte_length_static(cls) -> int:
        return cls.bit_size() // NUM_BITS_IN_BYTE

    @classmethod
    def storage_type(cls) -> TealType:
        return uint_storage_type(cls.bit_size())

    @classmethod
    def __str__(cls) -> str:
        return "uint{}".format(cls.bit_size())

    @classmethod
    @abstractmethod
    def bit_size(cls) -> int:
        pass

    def get(self) -> Expr:
        return self.stored_value.load()

    def set(self, value: Union[int, Expr, "Uint"]) -> Expr:
        if isinstance(value, Type) and not self.has_same_type_as(value):
            raise TealInputError("Cannot set type {} to {}".format(self, value))
        return uint_set(self.bit_size(), self.stored_value, value)

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None
    ) -> Expr:
        return uint_decode(
            self.bit_size(), self.stored_value, encoded, startIndex, endIndex, length
        )

    def encode(self) -> Expr:
        return uint_encode(self.bit_size(), self.stored_value)


Uint.__module__ = "pyteal"

Uint8 = Uint[Literal[8]]
Uint16 = Uint[Literal[16]]
Uint32 = Uint[Literal[32]]
Uint64 = Uint[Literal[64]]


class Byte(Uint8):
    @classmethod
    def __str__(cls) -> str:
        return "byte"


Byte.__module__ = "pyteal"
