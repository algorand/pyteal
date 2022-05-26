from typing import (
    TypeVar,
    Union, cast
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


SIntTypeSpec.__module__ = "pyteal"


class SInt8TypeSpec(SIntTypeSpec):
    def __init__(self):
        super().__init__(8)

    def new_instance(self) -> "SInt8":
        return SInt8()

    def annotation_type(self) -> "type[SInt8]":
        return SInt8


SInt8TypeSpec.__module__ = "pyteal"


class SInt16TypeSpec(SIntTypeSpec):
    def __init__(self):
        super().__init__(16)

    def new_instance(self) -> "SInt16":
        return SInt16()

    def annotation_type(self) -> "type[SInt16]":
        return SInt16


SInt16TypeSpec.__module__ = "pyteal"


class SInt32TypeSpec(SIntTypeSpec):
    def __init__(self):
        super().__init__(32)

    def new_instance(self) -> "SInt32":
        return SInt32()

    def annotation_type(self) -> "type[SInt32]":
        return SInt32


SInt32TypeSpec.__module__ = "pyteal"


class SInt64TypeSpec(SIntTypeSpec):
    def __init__(self):
        super().__init__(64)

    def new_instance(self) -> "SInt64":
        return SInt64()

    def annotation_type(self) -> "type[SInt64]":
        return SInt64


SInt64TypeSpec.__module__ = "pyteal"


T = TypeVar("T", bound="Int")


def twos_complement(x: int, bit_size: int) -> int:
    return ((abs(x) ^ (2 ** bit_size - 1)) + 1) % 2 ** bit_size


class SInt(Uint):
    @abstractmethod
    def __init__(self, spec: SIntTypeSpec) -> None:
        super().__init__(spec)

    # PLEASE NOTE: It's not necessary to change this inherited method.
    # This is an abstract class so as long as all the children of this class return a concrete SIntTypeSpec,
    #  there's no way that a SInt could return a UintTypeSpec.
    # Even if we could actually instantiate a generic SInt, it would still be correct for it to have
    #  signature -> UintTypeSpec and return a SIntTypeSpec.
    # def type_spec(self) -> SIntTypeSpec:
    #     return cast(SIntTypeSpec, super().type_spec())

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

    # FIXME: Eh, I'm not too happy with this code. This is here only to re-frame the raised error.
    #  I don't know if that's enough to justify overriding this method.
    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None,
    ) -> Expr:
        try:
            return super().decode(encoded, startIndex=startIndex, endIndex=endIndex, length=length)
        except NotImplementedError:
            raise NotImplementedError("SInt operations have not yet been implemented for bit sizes larger than 64")
        except ValueError:
            raise ValueError("Unsupported SInt size: {}".format(self.type_spec().bit_size()))

    def encode(self) -> Expr:
        try:
            return super().encode()
        except NotImplementedError:
            raise NotImplementedError("SInt operations have not yet been implemented for bit sizes larger than 64")
        except ValueError:
            raise ValueError("Unsupported SInt size: {}".format(self.type_spec().bit_size()))


SInt.__module__ = "pyteal"


class SInt8(SInt):
    def __init__(self) -> None:
        super().__init__(SInt8TypeSpec())


SInt8.__module__ = "pyteal"


class SInt16(SInt):
    def __init__(self) -> None:
        super().__init__(SInt16TypeSpec())


SInt16.__module__ = "pyteal"


class SInt32(SInt):
    def __init__(self) -> None:
        super().__init__(SInt32TypeSpec())


SInt32.__module__ = "pyteal"


class SInt64(SInt):
    def __init__(self) -> None:
        super().__init__(SInt64TypeSpec())


SInt64.__module__ = "pyteal"
