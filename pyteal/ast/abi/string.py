from typing import Union

from .type import ComputedValue, TypeSpec
from pyteal.types import require_type
from .array_dynamic import DynamicArray, DynamicArrayTypeSpec
from .uint import ByteTypeSpec, Uint16TypeSpec
from .util import substringForDecoding

from ..bytes import Bytes
from ..unaryexpr import Itob
from ..substring import Suffix
from ...types import TealType, require_type
from ...errors import TealInputError
from ..int import Int
from ..expr import Expr
from ..seq import Seq
from ..naryexpr import Concat


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

    def set(self, value: Union[str, "String", ComputedValue["String"], Expr]):
        if isinstance(value, ComputedValue):
            return value.store_into(self)

        if isinstance(value, String):
            return self.decode(value.encode())

        if type(value) is str:
            # Assume not prefixed with length
            value = Concat(
                Suffix(Itob(Int(len(value))), Int(6)),
                Bytes(value)
            )

        if not isinstance(value, Expr):
            raise TealInputError("Expected Expr, got {}".format(value))

        # TODO: should we prefix this with length?
        return self.stored_value.store(value)

    def __getitem__(self, index: Union[int, slice, Expr]) -> "ComputedValue[String]":

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

        return SubstringValue(self, start, stop)


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
