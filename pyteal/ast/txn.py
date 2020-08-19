from enum import Enum

from ..types import TealType
from ..errors import TealInputError
from ..ir import TealOp, Op
from .leafexpr import LeafExpr
from .int import EnumInt

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

class Txna(LeafExpr):
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

class Txn(LeafExpr):
    """An expression that accesses a transaction field from the current transaction."""

    def __init__(self, field: TxnField) -> None:
        self.field = field

    def __str__(self):
        return "(Txn {})".format(self.field.arg_name)

    def __teal__(self):
        return [TealOp(Op.txn, self.field.arg_name)]
    
    def type_of(self):
        return self.field.type_of()

    @classmethod
    def sender(cls):
        """Get the 32 byte address of the sender."""
        return cls(TxnField.sender)

    @classmethod
    def fee(cls):
        """Get the transaction fee in micro Algos."""
        return cls(TxnField.fee)

    @classmethod
    def first_valid(cls):
        """Get the first valid round number."""
        return cls(TxnField.first_valid)
   
    @classmethod
    def last_valid(cls):
        """Get the last valid round number."""
        return cls(TxnField.last_valid)

    @classmethod
    def note(cls):
        """Get the transaction note."""
        return cls(TxnField.note)

    @classmethod
    def lease(cls):
        """Get the transaction lease."""
        return cls(TxnField.lease)
   
    @classmethod
    def receiver(cls):
        """Get the 32 byte address of the receiver."""
        return cls(TxnField.receiver)

    @classmethod
    def amount(cls):
        """Get the amount of the transaction in micro Algos."""
        return cls(TxnField.amount)

    @classmethod
    def close_remainder_to(cls):
        """Get the 32 byte address of the CloseRemainderTo field."""
        return cls(TxnField.close_remainder_to)

    @classmethod
    def vote_pk(cls):
        return cls(TxnField.vote_pk)

    @classmethod
    def selection_pk(cls):
        return cls(TxnField.selection_pk)

    @classmethod
    def vote_first(cls):
        return cls(TxnField.vote_first)

    @classmethod
    def vote_last(cls):
        return cls(TxnField.vote_last)

    @classmethod
    def vote_key_dilution(cls):
        return cls(TxnField.vote_key_dilution)

    @classmethod
    def type(cls):
        return cls(TxnField.type)

    @classmethod
    def type_enum(cls):
        """Get the type of this transaction.
        
        See the TxnType enum for possible values.
        """
        return cls(TxnField.type_enum)

    @classmethod
    def xfer_asset(cls):
        """The ID of the asset being transferred."""
        return cls(TxnField.xfer_asset)

    @classmethod
    def asset_amount(cls):
        """The the amount of the asset being transferred, measured in the asset's units."""
        return cls(TxnField.asset_amount)

    @classmethod
    def asset_sender(cls):
        """Get the 32 byte address of the subject of clawback.
        
        The transaction will clawback of all of an asset from this address if the transaction sender
        is the clawback address of the asset.
        """
        return cls(TxnField.asset_sender)

    @classmethod
    def asset_receiver(cls):
        return cls(TxnField.asset_receiver)

    @classmethod
    def asset_close_to(cls):
        return cls(TxnField.asset_close_to)

    @classmethod
    def group_index(cls):
        """Get the position of the current transaction within the atomic transaction group.
        
        A stand-alone transaction is implictly element 0 in a group of 1.
        """
        return cls(TxnField.group_index)

    @classmethod
    def tx_id(cls):
        """Get the 32 byte computed ID for the current transaction."""
        return cls(TxnField.tx_id)
    
    @classmethod
    def application_id(cls):
        """Get the application ID from the ApplicationCall portion of the current transaction."""
        return cls(TxnField.application_id)

    @classmethod
    def on_completion(cls):
        """Get the on completion action from the ApplicationCall portion of the current transaction."""
        return cls(TxnField.on_completion)

    @classmethod
    def approval_program(cls):
        """Get the approval program."""
        return cls(TxnField.approval_program)
    
    @classmethod
    def clear_state_program(cls):
        """Get the clear state program."""
        return cls(TxnField.clear_state_program)
    
    @classmethod
    def rekey_to(cls):
        """Get the sender's new 32 byte AuthAddr"""
        return cls(TxnField.rekey_to)
    
    @classmethod
    def config_asset(cls):
        """Get the asset ID in asset config transaction."""
        return cls(TxnField.config_asset)
    
    @classmethod
    def config_asset_total(cls):
        """Get the total number of units of this asset created."""
        return cls(TxnField.config_asset_total)

    @classmethod
    def config_asset_decimals(cls):
        """Get the number of digits to display after the decimal place when displaying the asset."""
        return cls(TxnField.config_asset_decimals)
    
    @classmethod
    def config_asset_default_frozen(cls):
        """Check if the asset's slots are frozen by default or not."""
        return cls(TxnField.config_asset_default_frozen)
    
    @classmethod
    def config_asset_unit_name(cls):
        """Get the unit name of the asset."""
        return cls(TxnField.config_asset_unit_name)

    @classmethod
    def config_asset_name(cls):
        """Get the asset name."""
        return cls(TxnField.config_asset_name)
    
    @classmethod
    def config_asset_url(cls):
        """Get the asset URL."""
        return cls(TxnField.config_asset_url)
    
    @classmethod
    def config_asset_metadata_hash(cls):
        """Get the 32 byte commitment to some unspecified asset metdata."""
        return cls(TxnField.config_asset_metadata_hash)
    
    @classmethod
    def config_asset_manager(cls):
        """Get the 32 byte asset manager address."""
        return cls(TxnField.config_asset_manager)
    
    @classmethod
    def config_asset_reserve(cls):
        """Get the 32 byte asset reserve address."""
        return cls(TxnField.config_asset_reserve)
    
    @classmethod
    def config_asset_freeze(cls):
        """Get the 32 byte asset freeze address."""
        return cls(TxnField.config_asset_freeze)
    
    @classmethod
    def config_asset_clawback(cls):
        """Get the 32 byte asset clawback address."""
        return cls(TxnField.config_asset_clawback)
    
    @classmethod
    def freeze_asset(cls):
        """Get the asset ID being frozen or un-frozen."""
        return cls(TxnField.freeze_asset)
    
    @classmethod
    def freeze_asset_account(cls):
        """Get the 32 byte address of the account whose asset slot is being frozen or un-frozen."""
        return cls(TxnField.freeze_asset_account)
    
    @classmethod
    def freeze_asset_frozen(cls):
        """Get the new frozen value for the asset."""
        return cls(TxnField.freeze_asset_frozen)
    
    class ArrayAccessor:

        def __init__(self, accessField: TxnField, lengthField: TxnField) -> None:
            self.accessField = accessField
            self.lengthField = lengthField
        
        def length(self):
            """Get the length of this array."""
            return Txn(self.lengthField)
        
        def __getitem__(self, index: int):
            """Get the value at an index in this array.
            
            Args:
                index: Must not be negative.
            """
            if not isinstance(index, int) or index < 0:
                raise TealInputError("Invalid array index: {}".format(index))

            return Txna(self.accessField, index)
    
    """Application args array"""
    application_args = ArrayAccessor(TxnField.application_args, TxnField.num_app_args)

    """Accounts array"""
    accounts = ArrayAccessor(TxnField.accounts, TxnField.num_accounts)
