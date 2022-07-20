from typing import Final

from pyteal.types import TealType, require_type
from pyteal.ir import Op
from pyteal.ast.expr import Expr
from pyteal.ast.maybe import MaybeValue


class AssetHolding:
    @classmethod
    def balance(cls, account: Expr, asset: Expr) -> MaybeValue:
        """Get the amount of an asset held by an account.

        Args:
            account: An index into Txn.Accounts that corresponds to the account to check,
                must be evaluated to uint64 (or, since v4, an account address that appears in
                Txn.Accounts or is Txn.Sender, must be evaluated to bytes).
            asset: The ID of the asset to get, must be evaluated to uint64 (or, since v4,
                a Txn.assets offset).
        """
        require_type(account, TealType.anytype)
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_holding_get,
            TealType.uint64,
            immediate_args=["AssetBalance"],
            args=[account, asset],
        )

    @classmethod
    def frozen(cls, account: Expr, asset: Expr) -> MaybeValue:
        """Check if an asset is frozen for an account.

        A value of 1 indicates frozen and 0 indicates not frozen.

        Args:
            account: An index into Txn.Accounts that corresponds to the account to check,
                must be evaluated to uint64 (or, since v4, an account address that appears in
                Txn.Accounts or is Txn.Sender, must be evaluated to bytes).
            asset: The ID of the asset to get, must be evaluated to uint64 (or, since v4,
                a Txn.assets offset).
        """
        require_type(account, TealType.anytype)
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_holding_get,
            TealType.uint64,
            immediate_args=["AssetFrozen"],
            args=[account, asset],
        )


AssetHolding.__module__ = "pyteal"


class AssetHoldingObject:
    """Represents information about an account's holding of an asset"""

    def __init__(self, asset: Expr, account: Expr) -> None:
        """Create a new AssetParamObject for the given asset.

        Args:
            asset: An identifier for the asset. It must be an index into Txn.ForeignAssets that
                corresponds to the asset to check, or since v4, an asset ID that appears in
                Txn.ForeignAssets. In either case, it must evaluate to uint64.
            account: An identifier for the account. It must be an index into Txn.Accounts that
                corresponds to the account to check (in which case it must evaluate to uint64), or
                since v4, an account address that appears in Txn.Accounts or is Txn.Sender (in which
                case it must evaluate to bytes).
        """
        require_type(asset, TealType.uint64)
        self._asset: Final = asset
        require_type(account, TealType.anytype)
        self._account: Final = account

    def balance(self) -> MaybeValue:
        """Get the amount of the asset held by the account."""
        return AssetHolding.balance(self._account, self._asset)

    def frozen(self) -> MaybeValue:
        """Check if the asset is frozen for the account.

        A value of 1 indicates frozen and 0 indicates not frozen.
        """
        return AssetHolding.frozen(self._account, self._asset)


AssetHoldingObject.__module__ = "pyteal"


class AssetParam:
    @classmethod
    def total(cls, asset: Expr) -> MaybeValue:
        """Get the total number of units of an asset.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check,
                must be evaluated to uint64 (or since v4, an asset ID that appears in
                Txn.assets).
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.uint64,
            immediate_args=["AssetTotal"],
            args=[asset],
        )

    @classmethod
    def decimals(cls, asset: Expr) -> MaybeValue:
        """Get the number of decimals for an asset.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check,
                must be evaluated to uint64 (or since v4, an asset ID that appears in
                Txn.assets).
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.uint64,
            immediate_args=["AssetDecimals"],
            args=[asset],
        )

    @classmethod
    def defaultFrozen(cls, asset: Expr) -> MaybeValue:
        """Check if an asset is frozen by default.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check,
                must be evaluated to uint64 (or since v4, an asset ID that appears in
                Txn.assets).
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.uint64,
            immediate_args=["AssetDefaultFrozen"],
            args=[asset],
        )

    @classmethod
    def unitName(cls, asset: Expr) -> MaybeValue:
        """Get the unit name of an asset.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check,
                must be evaluated to uint64 (or since v4, an asset ID that appears in
                Txn.assets).
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.bytes,
            immediate_args=["AssetUnitName"],
            args=[asset],
        )

    @classmethod
    def name(cls, asset: Expr) -> MaybeValue:
        """Get the name of an asset.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check,
                must be evaluated to uint64 (or since v4, an asset ID that appears in
                Txn.assets).
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.bytes,
            immediate_args=["AssetName"],
            args=[asset],
        )

    @classmethod
    def url(cls, asset: Expr) -> MaybeValue:
        """Get the URL of an asset.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check,
                must be evaluated to uint64 (or since v4, an asset ID that appears in
                Txn.assets).
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.bytes,
            immediate_args=["AssetURL"],
            args=[asset],
        )

    @classmethod
    def metadataHash(cls, asset: Expr) -> MaybeValue:
        """Get the arbitrary commitment for an asset.

        If set, this will be 32 bytes long.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check,
                must be evaluated to uint64 (or since v4, an asset ID that appears in
                Txn.assets).
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.bytes,
            immediate_args=["AssetMetadataHash"],
            args=[asset],
        )

    @classmethod
    def manager(cls, asset: Expr) -> MaybeValue:
        """Get the manager address for an asset.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check,
                must be evaluated to uint64 (or since v4, an asset ID that appears in
                Txn.assets).
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.bytes,
            immediate_args=["AssetManager"],
            args=[asset],
        )

    @classmethod
    def reserve(cls, asset: Expr) -> MaybeValue:
        """Get the reserve address for an asset.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check,
                must be evaluated to uint64 (or since v4, an asset ID that appears in
                Txn.assets).
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.bytes,
            immediate_args=["AssetReserve"],
            args=[asset],
        )

    @classmethod
    def freeze(cls, asset: Expr) -> MaybeValue:
        """Get the freeze address for an asset.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check,
                must be evaluated to uint64 (or since v4, an asset ID that appears in
                Txn.assets).
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.bytes,
            immediate_args=["AssetFreeze"],
            args=[asset],
        )

    @classmethod
    def clawback(cls, asset: Expr) -> MaybeValue:
        """Get the clawback address for an asset.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check,
                must be evaluated to uint64 (or since v4, an asset ID that appears in
                Txn.assets).
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.bytes,
            immediate_args=["AssetClawback"],
            args=[asset],
        )

    @classmethod
    def creator(cls, asset: Expr) -> MaybeValue:
        """Get the creator address for an asset.

        Args:
            asset: An index into Txn.assets that corresponds to the asset to check. Must
                evaluate to uint64.
        """
        require_type(asset, TealType.uint64)
        return MaybeValue(
            Op.asset_params_get,
            TealType.bytes,
            immediate_args=["AssetCreator"],
            args=[asset],
        )


AssetParam.__module__ = "pyteal"


class AssetParamObject:
    """Represents information about an asset's parameters"""

    def __init__(self, asset: Expr) -> None:
        """Create a new AssetParamObject for the given asset.

        Args:
            asset: An identifier for the asset. It must be an index into Txn.ForeignAssets that
                corresponds to the asset to check, or since v4, an asset ID that appears in
                Txn.ForeignAssets. In either case, it must evaluate to uint64.
        """
        require_type(asset, TealType.uint64)
        self._asset: Final = asset

    def total(self) -> MaybeValue:
        """Get the total number of units of the asset."""
        return AssetParam.total(self._asset)

    def decimals(self) -> MaybeValue:
        """Get the number of decimals for the asset."""
        return AssetParam.decimals(self._asset)

    def default_frozen(self) -> MaybeValue:
        """Check if the asset is frozen by default."""
        return AssetParam.defaultFrozen(self._asset)

    def unit_name(self) -> MaybeValue:
        """Get the unit name of the asset."""
        return AssetParam.unitName(self._asset)

    def name(self) -> MaybeValue:
        """Get the name of the asset."""
        return AssetParam.name(self._asset)

    def url(self) -> MaybeValue:
        """Get the URL of the asset."""
        return AssetParam.url(self._asset)

    def metadata_hash(self) -> MaybeValue:
        """Get the arbitrary commitment for the asset.

        If set, this will be 32 bytes long."""
        return AssetParam.metadataHash(self._asset)

    def manager_address(self) -> MaybeValue:
        """Get the manager address for the asset."""
        return AssetParam.manager(self._asset)

    def reserve_address(self) -> MaybeValue:
        """Get the reserve address for the asset."""
        return AssetParam.reserve(self._asset)

    def freeze_address(self) -> MaybeValue:
        """Get the freeze address for the asset."""
        return AssetParam.freeze(self._asset)

    def clawback_address(self) -> MaybeValue:
        """Get the clawback address for the asset."""
        return AssetParam.clawback(self._asset)

    def creator_address(self) -> MaybeValue:
        """Get the creator address for the asset."""
        return AssetParam.creator(self._asset)


AssetParamObject.__module__ = "pyteal"
