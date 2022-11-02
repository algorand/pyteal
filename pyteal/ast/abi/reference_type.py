from typing import Final, TypeVar, cast
from abc import abstractmethod
from pyteal.ast.abi.type import BaseType, TypeSpec
from pyteal.ast.abi.uint import NUM_BITS_IN_BYTE, uint_decode

from pyteal.ast.expr import Expr
from pyteal.ast.txn import Txn
from pyteal.ast.acct import AccountParamObject
from pyteal.ast.asset import AssetHoldingObject, AssetParamObject
from pyteal.ast.app import AppParamObject
from pyteal.errors import TealInputError
from pyteal.types import TealType


T = TypeVar("T", bound="ReferenceType")


class ReferenceTypeSpec(TypeSpec):
    @abstractmethod
    def new_instance(self) -> "ReferenceType":
        pass

    @abstractmethod
    def annotation_type(self) -> "type[ReferenceType]":
        pass

    def bit_size(self) -> int:
        """Get the bit size of the index this reference type holds"""
        return NUM_BITS_IN_BYTE

    def is_dynamic(self) -> bool:
        return False

    def byte_length_static(self) -> int:
        return 1

    def storage_type(self) -> TealType:
        return TealType.uint64


ReferenceTypeSpec.__module__ = "pyteal.abi"


class ReferenceType(BaseType):
    @abstractmethod
    def __init__(self, spec: ReferenceTypeSpec) -> None:
        super().__init__(spec)

    def type_spec(self) -> ReferenceTypeSpec:
        return cast(ReferenceTypeSpec, super().type_spec())

    def referenced_index(self) -> Expr:
        """Get the reference index for this value.

        The three reference types (account, application, asset) contain indexes into a foreign array
        of the transaction. This method returns that index.

        If this reference type is an application or asset, note that this DOES NOT return the
        application or asset ID. See :code:`application_id()` or :code:`asset_id()` for that.
        """
        return self.stored_value.load()

    def decode(
        self,
        encoded: Expr,
        *,
        start_index: Expr = None,
        end_index: Expr = None,
        length: Expr = None,
    ) -> Expr:
        return uint_decode(
            self.type_spec().bit_size(),
            self.stored_value,
            encoded,
            start_index,
            end_index,
            length,
        )

    def encode(self) -> Expr:
        raise TealInputError("A ReferenceType cannot be encoded")


ReferenceType.__module__ = "pyteal.abi"


class AccountTypeSpec(ReferenceTypeSpec):
    def new_instance(self) -> "Account":
        return Account()

    def annotation_type(self) -> "type[Account]":
        return Account

    def __str__(self) -> str:
        return "account"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AccountTypeSpec)


AccountTypeSpec.__module__ = "pyteal.abi"


class Account(ReferenceType):
    def __init__(self) -> None:
        super().__init__(AccountTypeSpec())

    def address(self) -> Expr:
        """Get the address of the account."""
        return Txn.accounts[self.stored_value.load()]

    def params(self) -> AccountParamObject:
        """Get information about the account."""
        return AccountParamObject(self.referenced_index())

    def asset_holding(self, asset: "Expr | Asset") -> AssetHoldingObject:
        """Get information about an asset held by this account.

        Args:
            asset: An identifier for the asset. It must be one of the following: an abi.Asset
                reference object, an expression holding an index into Txn.ForeignAssets that
                corresponds to the asset (in which case it must evaluate to uint64), or since v4, an
                expression holding an asset ID that appears in Txn.ForeignAssets (in which case it
                must evaluate to uint64).
        """
        if isinstance(asset, Asset):
            asset_ref = asset.referenced_index()
        else:
            asset_ref = asset
        return AssetHoldingObject(asset_ref, self.referenced_index())


Account.__module__ = "pyteal.abi"


class AssetTypeSpec(ReferenceTypeSpec):
    def new_instance(self) -> "Asset":
        return Asset()

    def annotation_type(self) -> "type[Asset]":
        return Asset

    def __str__(self) -> str:
        return "asset"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, AssetTypeSpec)


AssetTypeSpec.__module__ = "pyteal.abi"


class Asset(ReferenceType):
    def __init__(self) -> None:
        super().__init__(AssetTypeSpec())

    def asset_id(self) -> Expr:
        """Get the ID of the asset."""
        return Txn.assets[self.referenced_index()]

    def holding(self, account: Expr | Account) -> AssetHoldingObject:
        """Get information about this asset held by an account.

        Args:
            account: An identifier for the account. It must be one of the following: an abi.Account
                reference object, an expression holding an index into Txn.Accounts that corresponds
                to the account (in which case it must evaluate to uint64), or since v4, an
                expression holding an account address that appears in Txn.Accounts or is Txn.Sender
                (in which case it must evaluate to bytes).
        """
        if isinstance(account, Account):
            account_ref = account.referenced_index()
        else:
            account_ref = account
        return AssetHoldingObject(self.referenced_index(), account_ref)

    def params(self) -> AssetParamObject:
        """Get information about the asset's parameters."""
        return AssetParamObject(self.referenced_index())


Asset.__module__ = "pyteal.abi"


class ApplicationTypeSpec(ReferenceTypeSpec):
    def new_instance(self) -> "Application":
        return Application()

    def annotation_type(self) -> "type[Application]":
        return Application

    def __str__(self) -> str:
        return "application"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ApplicationTypeSpec)


ApplicationTypeSpec.__module__ = "pyteal.abi"


class Application(ReferenceType):
    def __init__(self) -> None:
        super().__init__(ApplicationTypeSpec())

    def application_id(self) -> Expr:
        """Get the ID of the application."""
        return Txn.applications[self.stored_value.load()]

    def params(self) -> AppParamObject:
        """Get information about the application's parameters."""
        return AppParamObject(self.referenced_index())


Application.__module__ = "pyteal.abi"


ReferenceTypeSpecs: Final[list[TypeSpec]] = [
    AccountTypeSpec(),
    AssetTypeSpec(),
    ApplicationTypeSpec(),
]
