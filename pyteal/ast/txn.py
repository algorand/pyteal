from enum import Enum
from typing import Callable

from ..types import TealType
from ..errors import TealInputError
from ..ir import TealOp, Op
from .leafexpr import LeafExpr
from .int import EnumInt
from .array import Array

class TxnType:
    """Enum of all possible transaction types."""
    Unknown = EnumInt("unknown")
    Payment = EnumInt("pay")
    KeyRegistration = EnumInt("keyreg")
    AssetConfig = EnumInt("acfg")
    AssetTransfer = EnumInt("axfer")
    AssetFreeze = EnumInt("afrz")
    ApplicationCall = EnumInt("appl")

class TxnField(Enum):
    sender = (0, "Sender", TealType.bytes)
    fee = (1, "Fee", TealType.uint64)
    first_valid = (2, "FirstValid", TealType.uint64)
    first_valid_time = (3, "FirstValidTime", TealType.uint64)
    last_valid = (4, "LastValid", TealType.uint64)
    note = (5, "Note", TealType.bytes)
    lease = (6, "Lease", TealType.bytes)
    receiver = (7, "Receiver", TealType.bytes)
    amount = (8, "Amount", TealType.uint64)
    close_remainder_to = (9, "CloseRemainderTo", TealType.bytes)
    vote_pk = (10, "VotePK", TealType.bytes)
    selection_pk = (11, "SelectionPK", TealType.bytes)
    vote_first = (12, "VoteFirst", TealType.uint64)
    vote_last = (13, "VoteLast", TealType.uint64)
    vote_key_dilution = (14, "VoteKeyDilution", TealType.uint64)
    type = (15, "Type", TealType.bytes)
    type_enum = (16, "TypeEnum", TealType.uint64)
    xfer_asset = (17, "XferAsset", TealType.uint64)
    asset_amount = (18, "AssetAmount", TealType.uint64)
    asset_sender = (19, "AssetSender", TealType.bytes)
    asset_receiver = (20, "AssetReceiver", TealType.bytes)
    asset_close_to = (21, "AssetCloseTo", TealType.bytes)
    group_index = (22, "GroupIndex", TealType.uint64)
    tx_id = (23, "TxID", TealType.bytes)
    application_id = (24, "ApplicationID", TealType.uint64)
    on_completion = (25, "OnCompletion", TealType.uint64)
    application_args = (26, "ApplicationArgs", TealType.bytes)
    num_app_args = (27, "NumAppArgs", TealType.uint64)
    accounts = (28, "Accounts", TealType.bytes)
    num_accounts = (2, "NumAccounts", TealType.uint64)
    approval_program = (30, "ApprovalProgram", TealType.bytes)
    clear_state_program = (31, "ClearStateProgram", TealType.bytes)
    rekey_to = (32, "RekeyTo", TealType.bytes)
    config_asset = (33, "ConfigAsset", TealType.uint64)
    config_asset_total = (34, "ConfigAssetTotal", TealType.uint64)
    config_asset_decimals = (35, "ConfigAssetDecimals", TealType.uint64)
    config_asset_default_frozen = (36, "ConfigAssetDefaultFrozen", TealType.uint64)
    config_asset_unit_name = (37, "ConfigAssetUnitName", TealType.bytes)
    config_asset_name = (38, "ConfigAssetName", TealType.bytes)
    config_asset_url = (39, "ConfigAssetURL", TealType.bytes)
    config_asset_metadata_hash = (40, "ConfigAssetMetadataHash", TealType.bytes)
    config_asset_manager = (41, "ConfigAssetManager", TealType.bytes)
    config_asset_reserve = (42, "ConfigAssetReserve", TealType.bytes)
    config_asset_freeze = (43, "ConfigAssetFreeze", TealType.bytes)
    config_asset_clawback = (44, "ConfigAssetClawback", TealType.bytes)
    freeze_asset = (45, "FreezeAsset", TealType.uint64)
    freeze_asset_account = (46, "FreezeAssetAccount", TealType.bytes)
    freeze_asset_frozen = (47, "FreezeAssetFrozen", TealType.uint64)

    def __init__(self, id: int, name: str, type: TealType) -> None:
        self.id = id
        self.arg_name = name
        self.ret_type = type
    
    def type_of(self) -> TealType:
        return self.ret_type

class TxnExpr(LeafExpr):
    """An expression that accesses a transaction field from the current transaction."""

    def __init__(self, field: TxnField) -> None:
        self.field = field

    def __str__(self):
        return "(Txn {})".format(self.field.arg_name)

    def __teal__(self):
        return [TealOp(Op.txn, self.field.arg_name)]
    
    def type_of(self):
        return self.field.type_of()

class TxnaExpr(LeafExpr):
    """An expression that accesses a transaction array field from the current transaction."""

    def __init__(self, field: TxnField, index: int) -> None:
        self.field = field
        self.index = index
    
    def __str__(self):
        return "(Txna {} {})".format(self.field.arg_name, self.index)
    
    def __teal__(self):
        return [TealOp(Op.txna, self.field.arg_name, self.index)]
    
    def type_of(self):
        return self.field.type_of()

class TxnArray(Array):
    """Represents a transaction array field."""

    def __init__(self, txnObject: 'TxnObject', accessField: TxnField, lengthField: TxnField) -> None:
        self.txnObject = txnObject
        self.accessField = accessField
        self.lengthField = lengthField
    
    def length(self) -> TxnExpr:
        return self.txnObject.txnType(self.lengthField)
    
    def __getitem__(self, index: int) -> TxnaExpr:
        if not isinstance(index, int) or index < 0:
            raise TealInputError("Invalid array index: {}".format(index))

        return self.txnObject.txnaType(self.accessField, index)

class TxnObject:
    """Represents a transaction and its fields."""

    def __init__(self, txnType: Callable[[TxnField], TxnExpr], txnaType: Callable[[TxnField, int], TxnaExpr]) -> None:
        self.txnType = txnType
        self.txnaType = txnaType

    def sender(self) -> TxnExpr:
        """Get the 32 byte address of the sender."""
        return self.txnType(TxnField.sender)
   
    def fee(self) -> TxnExpr:
        """Get the transaction fee in micro Algos."""
        return self.txnType(TxnField.fee)

    def first_valid(self) -> TxnExpr:
        """Get the first valid round number."""
        return self.txnType(TxnField.first_valid)
   
    def last_valid(self) -> TxnExpr:
        """Get the last valid round number."""
        return self.txnType(TxnField.last_valid)

    def note(self) -> TxnExpr:
        """Get the transaction note."""
        return self.txnType(TxnField.note)

    def lease(self) -> TxnExpr:
        """Get the transaction lease."""
        return self.txnType(TxnField.lease)

    def receiver(self) -> TxnExpr:
        """Get the 32 byte address of the receiver."""
        return self.txnType(TxnField.receiver)

    def amount(self) -> TxnExpr:
        """Get the amount of the transaction in micro Algos."""
        return self.txnType(TxnField.amount)

    def close_remainder_to(self) -> TxnExpr:
        """Get the 32 byte address of the CloseRemainderTo field."""
        return self.txnType(TxnField.close_remainder_to)

    def vote_pk(self) -> TxnExpr:
        return self.txnType(TxnField.vote_pk)

    def selection_pk(self) -> TxnExpr:
        return self.txnType(TxnField.selection_pk)

    def vote_first(self) -> TxnExpr:
        return self.txnType(TxnField.vote_first)

    def vote_last(self) -> TxnExpr:
        return self.txnType(TxnField.vote_last)

    def vote_key_dilution(self) -> TxnExpr:
        return self.txnType(TxnField.vote_key_dilution)

    def type(self) -> TxnExpr:
        return self.txnType(TxnField.type)

    def type_enum(self) -> TxnExpr:
        """Get the type of this transaction.
        
        See the TxnType enum for possible values.
        """
        return self.txnType(TxnField.type_enum)

    def xfer_asset(self) -> TxnExpr:
        """The ID of the asset being transferred."""
        return self.txnType(TxnField.xfer_asset)

    def asset_amount(self) -> TxnExpr:
        """The the amount of the asset being transferred, measured in the asset's units."""
        return self.txnType(TxnField.asset_amount)

    def asset_sender(self) -> TxnExpr:
        """Get the 32 byte address of the subject of clawback.
        
        The transaction will clawback of all of an asset from this address if the transaction sender
        is the clawback address of the asset.
        """
        return self.txnType(TxnField.asset_sender)

    def asset_receiver(self) -> TxnExpr:
        return self.txnType(TxnField.asset_receiver)

    def asset_close_to(self) -> TxnExpr:
        return self.txnType(TxnField.asset_close_to)

    def group_index(self) -> TxnExpr:
        """Get the position of the transaction within the atomic transaction group.
        
        A stand-alone transaction is implictly element 0 in a group of 1.
        """
        return self.txnType(TxnField.group_index)

    def tx_id(self) -> TxnExpr:
        """Get the 32 byte computed ID for the transaction."""
        return self.txnType(TxnField.tx_id)

    def application_id(self) -> TxnExpr:
        """Get the application ID from the ApplicationCall portion of the transaction."""
        return self.txnType(TxnField.application_id)

    def on_completion(self) -> TxnExpr:
        """Get the on completion action from the ApplicationCall portion of the transaction."""
        return self.txnType(TxnField.on_completion)

    def approval_program(self) -> TxnExpr:
        """Get the approval program."""
        return self.txnType(TxnField.approval_program)

    def clear_state_program(self) -> TxnExpr:
        """Get the clear state program."""
        return self.txnType(TxnField.clear_state_program)

    def rekey_to(self) -> TxnExpr:
        """Get the sender's new 32 byte AuthAddr"""
        return self.txnType(TxnField.rekey_to)

    def config_asset(self) -> TxnExpr:
        """Get the asset ID in asset config transaction."""
        return self.txnType(TxnField.config_asset)

    def config_asset_total(self) -> TxnExpr:
        """Get the total number of units of this asset created."""
        return self.txnType(TxnField.config_asset_total)

    def config_asset_decimals(self) -> TxnExpr:
        """Get the number of digits to display after the decimal place when displaying the asset."""
        return self.txnType(TxnField.config_asset_decimals)

    def config_asset_default_frozen(self) -> TxnExpr:
        """Check if the asset's slots are frozen by default or not."""
        return self.txnType(TxnField.config_asset_default_frozen)

    def config_asset_unit_name(self) -> TxnExpr:
        """Get the unit name of the asset."""
        return self.txnType(TxnField.config_asset_unit_name)

    def config_asset_name(self) -> TxnExpr:
        """Get the asset name."""
        return self.txnType(TxnField.config_asset_name)

    def config_asset_url(self) -> TxnExpr:
        """Get the asset URL."""
        return self.txnType(TxnField.config_asset_url)

    def config_asset_metadata_hash(self) -> TxnExpr:
        """Get the 32 byte commitment to some unspecified asset metdata."""
        return self.txnType(TxnField.config_asset_metadata_hash)

    def config_asset_manager(self) -> TxnExpr:
        """Get the 32 byte asset manager address."""
        return self.txnType(TxnField.config_asset_manager)

    def config_asset_reserve(self) -> TxnExpr:
        """Get the 32 byte asset reserve address."""
        return self.txnType(TxnField.config_asset_reserve)

    def config_asset_freeze(self) -> TxnExpr:
        """Get the 32 byte asset freeze address."""
        return self.txnType(TxnField.config_asset_freeze)

    def config_asset_clawback(self) -> TxnExpr:
        """Get the 32 byte asset clawback address."""
        return self.txnType(TxnField.config_asset_clawback)

    def freeze_asset(self) -> TxnExpr:
        """Get the asset ID being frozen or un-frozen."""
        return self.txnType(TxnField.freeze_asset)

    def freeze_asset_account(self) -> TxnExpr:
        """Get the 32 byte address of the account whose asset slot is being frozen or un-frozen."""
        return self.txnType(TxnField.freeze_asset_account)

    def freeze_asset_frozen(self) -> TxnExpr:
        """Get the new frozen value for the asset."""
        return self.txnType(TxnField.freeze_asset_frozen)

    @property
    def application_args(self) -> TxnArray:
        """Application arguments array."""
        return TxnArray(self, TxnField.application_args, TxnField.num_app_args)

    @property
    def accounts(self) -> TxnArray:
        """Accounts array."""
        return TxnArray(self, TxnField.accounts, TxnField.num_accounts)

Txn: TxnObject = TxnObject(TxnExpr, TxnaExpr)
