from typing import (
    TypeVar,
    cast,
    Union
)
from abc import abstractmethod

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


class SInt16TypeSpec(SIntTypeSpec):
    def __init__(self):
        super().__init__(16)

    def new_instance(self) -> "SInt16":
        return SInt16()

    def annotation_type(self) -> "type[SInt16]":
        return SInt16


T = TypeVar("T", bound="Int")


def twos_complement(x: int, bit_size: int) -> int:
    return ((abs(x) ^ (2 ** bit_size - 1)) + 1) % 2 ** bit_size


class SInt(Uint):
    @abstractmethod
    def __init__(self, spec: SIntTypeSpec) -> None:
        super().__init__(spec)

    def type_spec(self) -> SIntTypeSpec:
        return cast(SIntTypeSpec, super().type_spec())

    def set(self: T, value: Union[int, Expr, "SInt", ComputedValue[T]]) -> Expr:
        bit_size = self.type_spec().bit_size()
        min_int = -(2**bit_size)
        max_int = 2**bit_size - 1

        if isinstance(value, int) and min_int <= value <= max_int:
            if value < 0:
                value = twos_complement(value, self.type_spec().bit_size())
            value = Int(value)
        else:
            raise TealInputError("Value is not within {} and {} range of allowed values".format(min_int, max_int))

        if isinstance(value, Expr):
            # TODO: Continue implementing all input type cases.
            pass

        return Seq(
            self.stored_value.store(value)
        )


class SInt16(SInt):
    def __init__(self) -> None:
        super().__init__(SInt16TypeSpec())
