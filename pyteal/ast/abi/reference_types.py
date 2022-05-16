from abc import abstractmethod
from typing import cast, Any

from pyteal.errors import TealInputError

from pyteal.ast.expr import Expr
from pyteal.ast.txn import Txn

from pyteal.ast.abi.uint import Uint, UintTypeSpec


class ReferenceTypeSpec(UintTypeSpec):
    def __init__(self) -> None:
        return super().__init__(8)


ReferenceTypeSpec.__module__ = "pyteal"


class ReferenceType(Uint):
    def __init__(self, spec: ReferenceTypeSpec) -> None:
        super().__init__(spec)

    def type_spec(self) -> ReferenceTypeSpec:
        return cast(ReferenceTypeSpec, super().type_spec())

    @abstractmethod
    def get(self) -> Expr:
        return self.stored_value.load()


ReferenceType.__module__ = "pyteal"


class AccountTypeSpec(ReferenceTypeSpec):
    def new_instance(self) -> "Account":
        return Account()

    def __str__(self) -> str:
        return "account"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AccountTypeSpec)


AccountTypeSpec.__module__ = "pyteal"


class Account(ReferenceType):
    def __init__(self) -> None:
        super().__init__(AccountTypeSpec())

    def get(self) -> Expr:
        return Txn.accounts[self.stored_value.load()]

    def set(self, value: Any) -> Expr:
        # TODO: should we allow this on some InnerTxnBuilder?
        raise TealInputError("Cannot set account value")


Account.__module__ = "pyteal"


class AssetTypeSpec(ReferenceTypeSpec):
    def new_instance(self) -> "Asset":
        return Asset()

    def __str__(self) -> str:
        return "asset"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AssetTypeSpec)


AssetTypeSpec.__module__ = "pyteal"


class Asset(ReferenceType):
    def __init__(self) -> None:
        super().__init__(AssetTypeSpec())

    def get(self) -> Expr:
        return Txn.assets[self.stored_value.load()]

    def set(self, value: Any) -> Expr:
        # TODO: should we allow this on some InnerTxnBuilder?
        raise TealInputError("Cannot set account value")


Asset.__module__ = "pyteal"


class ApplicationTypeSpec(ReferenceTypeSpec):
    def new_instance(self) -> "Application":
        return Application()

    def __str__(self) -> str:
        return "application"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ApplicationTypeSpec)


ApplicationTypeSpec.__module__ = "pyteal"


class Application(ReferenceType):
    def __init__(self) -> None:
        super().__init__(ApplicationTypeSpec())

    def get(self) -> Expr:
        return Txn.applications[self.stored_value.load()]

    def set(self, value: Any) -> Expr:
        # TODO: should we allow this on some InnerTxnBuilder?
        raise TealInputError("Cannot set account value")


Application.__module__ = "pyteal"
