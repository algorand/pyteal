from .array_dynamic import DynamicArray, DynamicArrayTypeSpec
from .uint import ByteTypeSpec, Uint16TypeSpec
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
        return substringForDecoding(
            self.stored_value.load(),
            startIndex=Int(Uint16TypeSpec().byte_length_static()),
        )


String.__module__ = "pyteal"
