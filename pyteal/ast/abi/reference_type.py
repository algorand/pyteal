from typing import List, Final, TypeVar, Union, cast
from abc import abstractmethod
from pyteal.ast.abi.type import BaseType, ComputedValue, TypeSpec

from pyteal.ast.binaryexpr import GetByte
from pyteal.ast.bytes import Bytes
from pyteal.ast.int import Int
from pyteal.ast.expr import Expr
from pyteal.ast.ternaryexpr import SetByte
from pyteal.ast.txn import Txn
from pyteal.errors import TealInputError
from pyteal.types import TealType


T = TypeVar("T", bound="ReferenceType")


class ReferenceTypeSpec(TypeSpec):
    def __init__(self) -> None:
        super().__init__()
        self.size: Final = 8

    @abstractmethod
    def new_instance(self) -> "ReferenceType":
        pass

    @abstractmethod
    def annotation_type(self) -> "type[ReferenceType]":
        pass

    def bit_size(self) -> int:
        """Get the bit size of this uint type"""
        return self.size

    def is_dynamic(self) -> bool:
        return False

    def byte_length_static(self) -> int:
        return 1

    def storage_type(self) -> TealType:
        return TealType.uint64

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other)

    @abstractmethod
    def __str__(self) -> str:
        pass


class ReferenceType(BaseType):
    @abstractmethod
    def __init__(self, spec: ReferenceTypeSpec) -> None:
        super().__init__(spec)

    def type_spec(self) -> ReferenceTypeSpec:
        return cast(ReferenceTypeSpec, super().type_spec())

    def get(self) -> Expr:
        return self.stored_value.load()

    def set(
        self: T, value: Union[int, Expr, "ReferenceType", ComputedValue[T]]
    ) -> Expr:
        if isinstance(value, ComputedValue):
            return self._set_with_computed_type(value)

        if isinstance(value, BaseType) and not (
            isinstance(value.type_spec(), ReferenceTypeSpec)
        ):
            raise TealInputError(
                "Type {} is not assignable to type {}".format(
                    value.type_spec(), self.type_spec()
                )
            )

        match value:
            case int():
                return self.stored_value.store(Int(value))
            case Expr():
                return self.stored_value.store(value)
            case ReferenceType():
                return self.stored_value.store(value.get())
            case _:
                raise TealInputError(
                    "Expected int, Expr, ReferenceType or ComputedValue, got {}".format(
                        type(value)
                    )
                )

    def decode(
        self,
        encoded: Expr,
        *,
        startIndex: Expr = None,
        endIndex: Expr = None,
        length: Expr = None,
    ) -> Expr:
        if startIndex is None:
            startIndex = Int(0)
        return self.stored_value.store(GetByte(encoded, startIndex))

    def encode(self) -> Expr:
        return SetByte(Bytes(b"\x00"), Int(0), self.stored_value.load())


class AccountTypeSpec(ReferenceTypeSpec):
    def new_instance(self) -> "Account":
        return Account()

    def annotation_type(self) -> "type[Account]":
        return Account

    def __str__(self) -> str:
        return "account"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AccountTypeSpec)


AccountTypeSpec.__module__ = "pyteal"


class Account(ReferenceType):
    def __init__(self) -> None:
        super().__init__(AccountTypeSpec())

    def deref(self) -> Expr:
        return Txn.accounts[self.stored_value.load()]


Account.__module__ = "pyteal"


class AssetTypeSpec(ReferenceTypeSpec):
    def new_instance(self) -> "Asset":
        return Asset()

    def annotation_type(self) -> "type[Asset]":
        return Asset

    def __str__(self) -> str:
        return "asset"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AssetTypeSpec)


AssetTypeSpec.__module__ = "pyteal"


class Asset(ReferenceType):
    def __init__(self) -> None:
        super().__init__(AssetTypeSpec())

    def deref(self) -> Expr:
        return Txn.assets[self.stored_value.load()]


Asset.__module__ = "pyteal"


class ApplicationTypeSpec(ReferenceTypeSpec):
    def new_instance(self) -> "Application":
        return Application()

    def annotation_type(self) -> "type[Application]":
        return Application

    def __str__(self) -> str:
        return "application"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ApplicationTypeSpec)


ApplicationTypeSpec.__module__ = "pyteal"


class Application(ReferenceType):
    def __init__(self) -> None:
        super().__init__(ApplicationTypeSpec())

    def deref(self) -> Expr:
        return Txn.applications[self.stored_value.load()]


Application.__module__ = "pyteal"


ReferenceTypeSpecs: Final[List[TypeSpec]] = [
    AccountTypeSpec(),
    AssetTypeSpec(),
    ApplicationTypeSpec(),
]
