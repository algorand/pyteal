from typing import (
    TypeVar,
    Union
)
from abc import abstractmethod

from pyteal.ast.assert_ import Assert
from pyteal.ast.naryexpr import And
from pyteal.ast.seq import TealInputError, Seq
from pyteal.ast.int import Int
from pyteal.ast.expr import Expr
from pyteal.ast.abi.type import ComputedValue
from pyteal.ast.abi.uint import Uint, UintTypeSpec


class SIntTypeSpec(UintTypeSpec):
    @abstractmethod
    def new_instance(self) -> "SInt":
        pass

    @abstractmethod
    def annotation_type(self) -> "type[SInt]":
        pass


class SInt8TypeSpec(SIntTypeSpec):
    def __init__(self):
        super().__init__(8)

    def new_instance(self) -> "SInt8":
        return SInt8()

    def annotation_type(self) -> "type[SInt8]":
        return SInt8


class SInt16TypeSpec(SIntTypeSpec):
    def __init__(self):
        super().__init__(16)

    def new_instance(self) -> "SInt16":
        return SInt16()

    def annotation_type(self) -> "type[SInt16]":
        return SInt16


class SInt32TypeSpec(SIntTypeSpec):
    def __init__(self):
        super().__init__(32)

    def new_instance(self) -> "SInt32":
        return SInt32()

    def annotation_type(self) -> "type[SInt32]":
        return SInt32


class SInt64TypeSpec(SIntTypeSpec):
    def __init__(self):
        super().__init__(64)

    def new_instance(self) -> "SInt64":
        return SInt64()

    def annotation_type(self) -> "type[SInt64]":
        return SInt64


T = TypeVar("T", bound="Int")


def twos_complement(x: int, bit_size: int) -> int:
    return ((abs(x) ^ (2 ** bit_size - 1)) + 1) % 2 ** bit_size


class SInt(Uint):
    @abstractmethod
    def __init__(self, spec: SIntTypeSpec) -> None:
        super().__init__(spec)

    def set(self: T, value: Union[int, Expr, "SInt", ComputedValue[T]]) -> Expr:
        bit_size = self.type_spec().bit_size()
        min_int = -(2**(bit_size-1))
        max_int = 2**(bit_size-1) - 1

        if isinstance(value, int):
            if min_int <= value <= max_int:
                if value < 0:
                    value = twos_complement(value, bit_size)
            else:
                raise TealInputError("Value is not within {} and {} range of allowed values".format(min_int, max_int))
        elif isinstance(value, Expr) and not isinstance(value, SInt):
            return Seq(super().set(value), Assert(And(self.stored_value.load() <= Int(max_int))))

        return super().set(value)


class SInt8(SInt):
    def __init__(self) -> None:
        super().__init__(SInt8TypeSpec())


class SInt16(SInt):
    def __init__(self) -> None:
        super().__init__(SInt16TypeSpec())


class SInt32(SInt):
    def __init__(self) -> None:
        super().__init__(SInt32TypeSpec())


class SInt64(SInt):
    def __init__(self) -> None:
        super().__init__(SInt64TypeSpec())
