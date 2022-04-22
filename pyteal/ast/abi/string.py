from typing import Union, TypeVar, cast, Sequence

from pyteal.ast.abi.type import ComputedValue, TypeSpec, BaseType
from pyteal.ast.abi.array_base import ArrayElement
from pyteal.ast.abi.array_dynamic import DynamicArray, DynamicArrayTypeSpec
from pyteal.ast.abi.uint import ByteTypeSpec, Uint16TypeSpec
from pyteal.ast.abi.util import substringForDecoding

from pyteal.ast.int import Int
from pyteal.ast.expr import Expr
from pyteal.ast.bytes import Bytes
from pyteal.ast.unaryexpr import Itob, Len
from pyteal.ast.substring import Suffix
from pyteal.ast.int import Int
from pyteal.ast.expr import Expr
from pyteal.ast.naryexpr import Concat

from pyteal.types import TealType, require_type
from pyteal.errors import TealInputError


def encoded_string(s: Expr):
    return Concat(Suffix(Itob(Len(s)), Int(6)), s)

T = TypeVar("T", bound=BaseType)

class StringTypeSpec(DynamicArrayTypeSpec):
    def __init__(self) -> None:
        super().__init__(ByteTypeSpec())

    def new_instance(self) -> "String":
        return String()

    def __str__(self) -> str:
        return "string"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, StringTypeSpec)


StringTypeSpec.__module__ = "pyteal"


class String(DynamicArray):
    def __init__(self) -> None:
        super().__init__(StringTypeSpec())

    def type_spec(self) -> StringTypeSpec:
        return StringTypeSpec()

    def get(self) -> Expr:
        return Suffix(
            self.stored_value.load(), Int(Uint16TypeSpec().byte_length_static())
        )

    def set(self, value: Union[Sequence[T], DynamicArray[T], ComputedValue[DynamicArray[T]], "String", str, Expr]) -> Expr:

        # Assume length prefixed
        if isinstance(value, ComputedValue):
            if value.produced_type_spec() is not StringTypeSpec():
                raise TealInputError(f"Got ComputedValue with type spec {value.produced_type_spec()}, expected StringTypeSpec")
            return value.store_into(self)

        if isinstance(value, BaseType):
            if value.type_spec() is not StringTypeSpec():
                raise TealInputError(f"Got {value.__class__} with type spec {value.type_spec()}, expected StringTypeSpec")
            return value.decode(value.encode())

        # Assume not length prefixed
        if type(value) is str:
            return self.stored_value.store(encoded_string(Bytes(value)))

        if not isinstance(value, Expr):
            raise TealInputError("Expected Expr, got {}".format(value))

        return self.stored_value.store(encoded_string(value))

    def __getitem__(self, index: Union[int, slice, Expr]) -> "ArrayElement[T]":

        if type(index) is int or isinstance(index, Expr):
            return super().__getitem__(index)

        if type(index) is not slice:
            raise TealInputError("Index expected slice, got {index}")

        if index.step is not None:
            raise TealInputError("Slice step is not supported")

        start = index.start
        stop = index.stop

        if stop is not None and type(stop) is int and stop <= 0:
            raise TealInputError("Negative slice indicies are not supported")

        if start is not None and type(start) is int and start <= 0:
            raise TealInputError("Negative slice indicies are not supported")

        if stop is None:
            stop = self.length()

        if start is None:
            start = Int(0)

        if type(stop) is int:
            stop = Int(stop)

        if type(start) is int:
            start = Int(start)

        # TODO: ?????
        return ArrayElement(self, cast(Expr, SubstringValue(self, start, stop)))


String.__module__ = "pyteal"


class SubstringValue(ComputedValue):
    def __init__(self, string: String, start: Expr, stop: Expr) -> None:
        super().__init__()

        require_type(start, TealType.uint64)
        require_type(stop, TealType.uint64)

        self.string = string
        self.start = start
        self.stop = stop

    def produced_type_spec(cls) -> TypeSpec:
        return StringTypeSpec()

    def store_into(self, output: String) -> Expr:
        return output.decode(
            Concat(
                Suffix(Itob(self.stop - self.start), Int(6)),
                substringForDecoding(
                    self.string.get(), startIndex=self.start, endIndex=self.stop
                ),
            )
        )


SubstringValue.__module__ = "pyteal"
