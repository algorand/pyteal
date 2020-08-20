from enum import Enum

from ..types import TealType, require_type
from ..ir import TealOp, Op
from .expr import Expr
from .leafexpr import LeafExpr
from .maybe import MaybeValue

class AssetHolding:
    
    @classmethod
    def balance(cls, account: Expr, asset: Expr) -> MaybeValue:
        """Get the amount of an asset held by an account.

        Args:
            account: An index into Txn.Accounts that corresponds to the account to check. Must
                evaluate to uint64.
            asset: The ID of the asset to get. Must evaluate to uint64.
        """
        require_type(account.type_of(), TealType.uint64)
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_holding_get, TealType.uint64, immediate_args=["AssetBalance"], args=[account, asset])
    
    @classmethod
    def frozen(cls, account: Expr, asset: Expr) -> MaybeValue:
        """Check if an asset is frozen for an account.

        Args:
            account: An index into Txn.Accounts that corresponds to the account to check. Must
                evaluate to uint64.
            asset: The ID of the asset to check. Must evaluate to uint64.
        """
        require_type(account.type_of(), TealType.uint64)
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_holding_get, TealType.uint64, immediate_args=["AssetFrozen"], args=[account, asset])

AssetHolding.__module__ = "pyteal"

class AssetParam:

    @classmethod
    def total(cls, asset: Expr) -> MaybeValue:
        """Get the total number of units of an asset.

        Args:
            asset: An index into Txn.ForeignAssets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_params_get, TealType.uint64, immediate_args=["AssetTotal"], args=[asset])
    
    @classmethod
    def decimals(cls, asset: Expr) -> MaybeValue:
        """Get the number of decimals for an asset.

        Args:
            asset: An index into Txn.ForeignAssets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_params_get, TealType.uint64, immediate_args=["AssetDecimals"], args=[asset])
    
    @classmethod
    def defaultFrozen(cls, asset: Expr) -> MaybeValue:
        """Check if an asset is frozen by default.

        Args:
            asset: An index into Txn.ForeignAssets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_params_get, TealType.uint64, immediate_args=["AssetDefaultFrozen"], args=[asset])
    
    @classmethod
    def unitName(cls, asset: Expr) -> MaybeValue:
        """Get the unit name of an asset.

        Args:
            asset: An index into Txn.ForeignAssets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_params_get, TealType.bytes, immediate_args=["AssetUnitName"], args=[asset])
    
    @classmethod
    def name(cls, asset: Expr) -> MaybeValue:
        """Get the name of an asset.

        Args:
            asset: An index into Txn.ForeignAssets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_params_get, TealType.bytes, immediate_args=["AssetName"], args=[asset])
    
    @classmethod
    def url(cls, asset: Expr) -> MaybeValue:
        """Get the URL of an asset.

        Args:
            asset: An index into Txn.ForeignAssets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_params_get, TealType.bytes, immediate_args=["AssetURL"], args=[asset])
    
    @classmethod
    def metadataHash(cls, asset: Expr) -> MaybeValue:
        """Get the arbitrary commitment for an asset.

        Args:
            asset: An index into Txn.ForeignAssets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_params_get, TealType.bytes, immediate_args=["AssetMetadataHash"], args=[asset])
    
    @classmethod
    def manager(cls, asset: Expr) -> MaybeValue:
        """Get the manager commitment for an asset.

        Args:
            asset: An index into Txn.ForeignAssets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_params_get, TealType.bytes, immediate_args=["AssetManager"], args=[asset])
    
    @classmethod
    def reserve(cls, asset: Expr) -> MaybeValue:
        """Get the reserve address for an asset.

        Args:
            asset: An index into Txn.ForeignAssets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_params_get, TealType.bytes, immediate_args=["AssetReserve"], args=[asset])
    
    @classmethod
    def freeze(cls, asset: Expr) -> MaybeValue:
        """Get the freeze address for an asset.

        Args:
            asset: An index into Txn.ForeignAssets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_params_get, TealType.bytes, immediate_args=["AssetFreeze"], args=[asset])
    
    @classmethod
    def clawback(cls, asset: Expr) -> MaybeValue:
        """Get the clawback address for an asset.

        Args:
            asset: An index into Txn.ForeignAssets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset.type_of(), TealType.uint64)
        return MaybeValue(Op.asset_params_get, TealType.bytes, immediate_args=["AssetClawback"], args=[asset])

AssetParam.__module__ = "pyteal"
