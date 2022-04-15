from typing import Union
from .array_static import StaticArray, StaticArrayTypeSpec
from .array_dynamic import DynamicArray, DynamicArrayTypeSpec
from .uint import ByteTypeSpec
from .util import substringForDecoding

from ..int import Int
from ..expr import Expr


class StringTypeSpec(DynamicArrayTypeSpec):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec())

    def new_instance(self) -> "String":
        return String()

    def __str__(self) -> str:
        return "string"


StringTypeSpec.__module__ = "pyteal"


class String(DynamicArray):
    def __init__(self) -> None:
        super().__init__(StringTypeSpec())

    def type_spec(self) -> StringTypeSpec:
        return StringTypeSpec()

    def get(self) -> Expr:
        return substringForDecoding(self.stored_value.load(), startIndex=Int(2))

    def __getslice__(self, low: Union[int, Int], high: Union[int, Int]):
        if type(low) is int:
            low = Int(low)

        if type(high) is int:
            high = Int(high)

        if not isinstance(low, Int):
            raise TypeError("low expected int or Int, got {low}")
        if not isinstance(high, Int):
            raise TypeError("high expected int or Int, got {high}")

        return substringForDecoding(
            self.stored_value.load(), startIndex=Int(2) + low, endIndex=Int(2) + high
        )


String.__module__ = "pyteal"
