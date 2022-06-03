from typing import (
    TypeVar,
    Union,
    Final
)
from abc import abstractmethod

from pyteal.ast.expr import Expr
from pyteal.ast.abi.type import ComputedValue
from pyteal.ast.abi.uint import Uint, UintTypeSpec


class FixedPointTypeSpec(UintTypeSpec):
    def __init__(self, bit_size: int, fractional_size: int):
        super().__init__(bit_size)
        if fractional_size >= self.size:
            raise TypeError("Unsupported fractional size. Must be less than total bit size.")
        self.fractional_size: Final = fractional_size

    @abstractmethod
    def new_instance(self) -> "FixedPoint":
        pass
    
    def annotation_type(self) -> "type[FixedPoint]":
        pass


FixedPointTypeSpec.__module__ = "pyteal"


class FixedPoint8TypeSpec(FixedPointTypeSpec):
    def __init__(self, fractional_size: int):
        super().__init__(8, fractional_size)
    
    def new_instance(self) -> "FixedPoint":
        return FixedPoint8()
    
    def annotation_type(self) -> "type[FixedPoint]":
        return FixedPoint8


FixedPoint8TypeSpec.__module__ = "pyteal"


class FixedPoint16TypeSpec(FixedPointTypeSpec):
    def __init__(self, fractional_size: int):
        super().__init__(16, fractional_size)
    
    def new_instance(self) -> "FixedPoint":
        return FixedPoint16()
    
    def annotation_type(self) -> "type[FixedPoint]":
        return FixedPoint16


FixedPoint16TypeSpec.__module__ = "pyteal"


class FixedPoint32TypeSpec(FixedPointTypeSpec):
    def __init__(self, fractional_size: int):
        super().__init__(32, fractional_size)
    
    def new_instance(self) -> "FixedPoint":
        return FixedPoint32()
    
    def annotation_type(self) -> "type[FixedPoint]":
        return FixedPoint32


FixedPoint32TypeSpec.__module__ = "pyteal"


class FixedPoint64TypeSpec(FixedPointTypeSpec):
    def __init__(self, fractional_size: int):
        super().__init__(64, fractional_size)

    def new_instance(self) -> "FixedPoint":
        return FixedPoint64()

    def annotation_type(self) -> "type[FixedPoint]":
        return FixedPoint64


FixedPoint64TypeSpec.__module__ = "pyteal"


T = TypeVar("T", bound="FixedPoint")


class FixedPoint(Uint):
    @abstractmethod
    def __init__(self, spec: FixedPointTypeSpec) -> None:
        super().__init__(spec)

    def set(self: T, value: Union[int, Expr, "Uint", ComputedValue[T]]) -> Expr:
        pass

    def type_spec(self) -> UintTypeSpec:
        pass

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None,
    ) -> Expr:
        pass

    def encode(self) -> Expr:
        pass


FixedPoint.__module__ = "pyteal"


class FixedPoint8(FixedPoint):
    def __init__(self, fractional_size: int):
        super().__init__(FixedPoint8TypeSpec(fractional_size))


FixedPoint8.__module__ = "pyteal"


class FixedPoint16(FixedPoint):
    def __init__(self, fractional_size: int):
        super().__init__(FixedPoint8TypeSpec(fractional_size))


FixedPoint16.__module__ = "pyteal"


class FixedPoint32(FixedPoint):
    def __init__(self, fractional_size: int):
        super().__init__(FixedPoint8TypeSpec(fractional_size))


FixedPoint32.__module__ = "pyteal"


class FixedPoint64(FixedPoint):
    def __init__(self, fractional_size: int):
        super().__init__(FixedPoint8TypeSpec(fractional_size))


FixedPoint64.__module__ = "pyteal"
