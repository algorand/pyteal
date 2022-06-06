from typing import List, Final
from pyteal.ast.abi.type import TypeSpec
from pyteal.ast.abi.uint import Uint, UintTypeSpec
from pyteal.ast.expr import Expr
from pyteal.ast.txn import Txn


class AccountTypeSpec(UintTypeSpec):
    def __init__(self):
        super().__init__(8)

    def new_instance(self) -> "Account":
        return Account()

    def annotation_type(self) -> "type[Account]":
        return Account

    def __str__(self) -> str:
        return "account"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AccountTypeSpec)


AccountTypeSpec.__module__ = "pyteal"


class Account(Uint):
    def __init__(self) -> None:
        super().__init__(AccountTypeSpec())

    def deref(self) -> Expr:
        return Txn.accounts[self.stored_value.load()]


Account.__module__ = "pyteal"


class AssetTypeSpec(UintTypeSpec):
    def __init__(self):
        super().__init__(8)

    def new_instance(self) -> "Asset":
        return Asset()

    def annotation_type(self) -> "type[Asset]":
        return Asset

    def __str__(self) -> str:
        return "asset"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AssetTypeSpec)


AssetTypeSpec.__module__ = "pyteal"


class Asset(Uint):
    def __init__(self) -> None:
        super().__init__(AssetTypeSpec())

    def deref(self) -> Expr:
        return Txn.assets[self.stored_value.load()]


Asset.__module__ = "pyteal"


class ApplicationTypeSpec(UintTypeSpec):
    def __init__(self):
        super().__init__(8)

    def new_instance(self) -> "Application":
        return Application()

    def annotation_type(self) -> "type[Application]":
        return Application

    def __str__(self) -> str:
        return "application"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ApplicationTypeSpec)


ApplicationTypeSpec.__module__ = "pyteal"


class Application(Uint):
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
