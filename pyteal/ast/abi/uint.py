from typing import (
    Union,
    Optional,
    Final,
    cast,
)
from abc import abstractmethod

from pyteal.types import TealType
from pyteal.errors import TealInputError
from pyteal.ast.abstractvar import AbstractVar
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


def uint_set(size: int, uint_var: AbstractVar, value: Union[int, Expr, "Uint"]) -> Expr:
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
        return uint_var.store(cast(Expr, value))

    return Seq(
        uint_var.store(cast(Expr, value)),
        Assert(uint_var.load() < Int(2**size)),
    )


def uint_decode(
    size: int,
    uint_var: AbstractVar,
    encoded: Expr,
    start_index: Optional[Expr],
    end_index: Optional[Expr],
    length: Optional[Expr],
) -> Expr:
    if size > 64:
        raise NotImplementedError(
            "Uint operations have not yet been implemented for bit sizes larger than 64"
        )

    if size == 64:
        if start_index is None:
            if end_index is None and length is None:
                return uint_var.store(Btoi(encoded))
            start_index = Int(0)
        return uint_var.store(ExtractUint64(encoded, start_index))

    if start_index is None:
        start_index = Int(0)

    if size == 8:
        return uint_var.store(GetByte(encoded, start_index))
    if size == 16:
        return uint_var.store(ExtractUint16(encoded, start_index))
    if size == 32:
        return uint_var.store(ExtractUint32(encoded, start_index))

    raise ValueError("Unsupported uint size: {}".format(size))


def uint_encode(size: int, uint_var: Expr | AbstractVar) -> Expr:
    if isinstance(uint_var, AbstractVar):
        uint_var = uint_var.load()

    if size > 64:
        raise NotImplementedError(
            "Uint operations have not yet been implemented for bit sizes larger than 64"
        )

    if size == 8:
        return SetByte(Bytes(b"\x00"), Int(0), uint_var)
    if size == 16:
        return Suffix(Itob(uint_var), Int(6))
    if size == 32:
        return Suffix(Itob(uint_var), Int(4))
    if size == 64:
        return Itob(uint_var)

    raise ValueError("Unsupported uint size: {}".format(size))


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


UintTypeSpec.__module__ = "pyteal.abi"


class ByteTypeSpec(UintTypeSpec):
    def __init__(self) -> None:
        super().__init__(8)

    def new_instance(self) -> "Byte":
        return Byte()

    def annotation_type(self) -> "type[Byte]":
        return Byte

    def __str__(self) -> str:
        return "byte"


ByteTypeSpec.__module__ = "pyteal.abi"


class Uint8TypeSpec(UintTypeSpec):
    def __init__(self) -> None:
        super().__init__(8)

    def new_instance(self) -> "Uint8":
        return Uint8()

    def annotation_type(self) -> "type[Uint8]":
        return Uint8


Uint8TypeSpec.__module__ = "pyteal.abi"


class Uint16TypeSpec(UintTypeSpec):
    def __init__(self) -> None:
        super().__init__(16)

    def new_instance(self) -> "Uint16":
        return Uint16()

    def annotation_type(self) -> "type[Uint16]":
        return Uint16


Uint16TypeSpec.__module__ = "pyteal.abi"


class Uint32TypeSpec(UintTypeSpec):
    def __init__(self) -> None:
        super().__init__(32)

    def new_instance(self) -> "Uint32":
        return Uint32()

    def annotation_type(self) -> "type[Uint32]":
        return Uint32


Uint32TypeSpec.__module__ = "pyteal.abi"


class Uint64TypeSpec(UintTypeSpec):
    def __init__(self) -> None:
        super().__init__(64)

    def new_instance(self) -> "Uint64":
        return Uint64()

    def annotation_type(self) -> "type[Uint64]":
        return Uint64


Uint64TypeSpec.__module__ = "pyteal.abi"


class Uint(BaseType):
    @abstractmethod
    def __init__(self, spec: UintTypeSpec) -> None:
        super().__init__(spec)

    def type_spec(self) -> UintTypeSpec:
        return cast(UintTypeSpec, super().type_spec())

    def get(self) -> Expr:
        """Return the value held by this Uint as a PyTeal expression.

        The expression will have the type TealType.uint64.
        """
        return self._stored_value.load()

    def set(self, value: Union[int, Expr, "Uint", ComputedValue["Uint"]]) -> Expr:
        """Set the value of this Uint to the input value.

        There are a variety of ways to express the input value. Regardless of the type used to
        indicate the input value, this Uint type can only hold values in the range :code:`[0,2^N)`,
        where :code:`N` is the bit size of this Uint.

        The behavior of this method depends on the input argument type:

            * :code:`int`: set the value to a Python integer. A compiler error will occur if this value overflows or underflows this integer type.
            * :code:`Expr`: set the value to the result of a PyTeal expression, which must evaluate to a TealType.uint64. The program will fail if the evaluated value overflows or underflows this integer type.
            * :code:`Uint`: copy the value from another Uint. The argument's type must exactly match this integer's type, otherwise an error will occur. For example, it's not possible to set a Uint64 to a Uint8, or vice versa.
            * :code:`ComputedValue[Uint]`: copy the value from a Uint produced by a ComputedValue. The type produced by the ComputedValue must exactly match this integer's type, otherwise an error will occur.

        Args:
            value: The new value this Uint should take. This must follow the above constraints.

        Returns:
            An expression which stores the given value into this Uint.
        """
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
        return uint_set(self.type_spec().bit_size(), self._stored_value, value)

    def decode(
        self,
        encoded: Expr,
        *,
        start_index: Expr | None = None,
        end_index: Expr | None = None,
        length: Expr | None = None,
    ) -> Expr:
        return uint_decode(
            self.type_spec().bit_size(),
            self._stored_value,
            encoded,
            start_index,
            end_index,
            length,
        )

    def encode(self) -> Expr:
        return uint_encode(self.type_spec().bit_size(), self._stored_value)


Uint.__module__ = "pyteal.abi"


class Byte(Uint):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec())


Byte.__module__ = "pyteal.abi"


class Uint8(Uint):
    def __init__(self) -> None:
        super().__init__(Uint8TypeSpec())


Uint8.__module__ = "pyteal.abi"


class Uint16(Uint):
    def __init__(self) -> None:
        super().__init__(Uint16TypeSpec())


Uint16.__module__ = "pyteal.abi"


class Uint32(Uint):
    def __init__(self) -> None:
        super().__init__(Uint32TypeSpec())


Uint32.__module__ = "pyteal.abi"


class Uint64(Uint):
    def __init__(self) -> None:
        super().__init__(Uint64TypeSpec())


Uint64.__module__ = "pyteal.abi"
